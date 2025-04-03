from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
import os
import tempfile
from reportlab.pdfgen import canvas
import re
import numpy as np
import configparser
from pydantic import BaseModel
from typing import Optional, List
import json

### Create FastAPI instance with custom docs and openapi url
app = FastAPI(docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")

# 遺伝子構造情報のモデルを追加
class GeneStructureInfo(BaseModel):
    transcript_id: str
    strand: str
    total_length: float
    exon_positions: List[int]
    five_prime_utr: float
    three_prime_utr: float

# リクエストモデルの定義を更新
class GeneStructureRequest(BaseModel):
    gene_id: str
    mode: str = "basic"
    file_name: Optional[str] = None
    utr_color: str = "#CCCCCC"
    exon_color: str = "#000000"
    line_color: str = "#000000"
    margin_x: int = 50
    margin_y: int = 50
    intron_shape: str = "straight"
    gene_h: int = 20
    domains: Optional[List[dict]] = None
    # ファイルの代わりに構造情報を追加
    gene_structure: Optional[GeneStructureInfo] = None

# 関数の定義
def get_transcript_id(gff_path, gene_id):
    if gff_path.endswith('.gff3'):
        transcript_id = []
        strand = []
        with open(gff_path, mode = 'r') as inp:
            for i, line in enumerate(inp):
                if line.startswith('#'):
                    pass
                else:
                    line = line.split('\t')
                    id_col = re.split('[:;]', line[8])

                    if len(id_col) < 4: continue
                    elif id_col[3] == gene_id:
                        transcript_id = id_col[1]
                        strand = line[6]

        return transcript_id, strand
    else:
        return False

def get_structure(gff_path, transcript_id):
    exon_pos = []
    exon_len = []
    total_length = 0
    five_prime_UTR = 0
    three_prime_UTR = 0

    with open(gff_path, mode = 'r') as inp: 
        for line in inp:
            line = line.rstrip('\r|\n|\r\n')
            if line.startswith('#'):
                pass
            else:
                line = line.split('\t')
                id_col = re.split('[:;]', line[8])
                if id_col[1] == transcript_id:
                    if line[2] == 'mRNA':
                        total_length = (int(line[4]) - int(line[3]))/10
                    elif line[2] == 'exon':
                        exon_pos.append(int(line[3]))
                        exon_pos.append(int(line[4]))
                        exon_len.append((int(line[4]) - int(line[3]))/10)
                    elif line[2] == 'five_prime_UTR':
                        five_prime_UTR = (int(line[4]) - int(line[3]))/10
                    elif line[2] == 'three_prime_UTR':
                        three_prime_UTR = (int(line[4]) - int(line[3]))/10
    
    return total_length, exon_pos, five_prime_UTR, three_prime_UTR

def cDNA_pos2gDNA_pos(cDNA_exon_pos, domain_cDNA_pos, cumsum_intron_len):
    x2 = np.sort(np.append(cDNA_exon_pos, domain_cDNA_pos))
    index = int(np.where(x2 == domain_cDNA_pos)[0])
    gDNA_pos = domain_cDNA_pos + cumsum_intron_len[index-1]
    return gDNA_pos

def color_convert(color16):
    color = color16.lstrip('#')
    color = list(color)

    lib = {'A':10, 'B':11, 'C':12, 'D':13, 'E':14, 'F':15,
            'a':10, 'b':11, 'c':12, 'd':13, 'e':14, 'f':15}

    for i,j in lib.items():
        for k,l in enumerate(color):
            if l == i:
                color[k] = j

    color = np.array([int(i) for i in color]).reshape(-1,2)
    RGB_255 = color @ np.array([16**1, 16**0]).T
    RGB_1 = RGB_255/255

    return RGB_1

@app.get("/api/py/")
def hello_fast_api():
    return {"message": "Hello from FastAPI"}

@app.post("/api/py/generate-gene-structure")
async def generate_gene_structure(request: GeneStructureRequest):
    try:
        # Vercel環境用の一時ディレクトリパスを設定
        temp_dir = '/tmp' if os.environ.get('VERCEL') == '1' else tempfile.gettempdir()
        
        # 一時ファイルの作成
        if not request.file_name:
            output_path = os.path.join(temp_dir, f"output_{os.urandom(8).hex()}.pdf")
            file_name = output_path
        else:
            file_name = request.file_name

        # クライアントから送信された構造情報を取得
        if not request.gene_structure:
            raise HTTPException(status_code=400, detail="遺伝子構造情報が提供されていません")
        
        # 構造情報の取り出し
        transcript_id = request.gene_structure.transcript_id
        strand = request.gene_structure.strand
        total_length = request.gene_structure.total_length
        exon_pos = request.gene_structure.exon_positions
        five_prime_UTR = request.gene_structure.five_prime_utr
        three_prime_UTR = request.gene_structure.three_prime_utr

        # エキソン＆イントロン長の計算
        if strand == '-':
            exon_intron_length = np.asarray([(exon_pos[i+1] - exon_pos[i])/10 for i in range(len(exon_pos)-1)])[::-1]
        else:
            exon_intron_length = np.asarray([(exon_pos[i+1] - exon_pos[i])/10 for i in range(len(exon_pos)-1)])

        exon_len = np.asarray([exon_intron_length[i] for i in range(len(exon_intron_length)) if i % 2 == 0])
        intron_len = np.asarray([exon_intron_length[i] for i in range(len(exon_intron_length)) if i % 2 == 1])

        # 累積イントロン長
        cumsum_intron_len = np.append(np.append(0, np.cumsum(intron_len)), 0)
        # cDNAでの位置
        cDNA_exon_pos = np.append(0, np.cumsum(exon_len))

        # 基本の作図用
        if strand == '-':
            x = np.abs(exon_pos - np.max(exon_pos))[::-1]/10 + 50
        else:
            x = (exon_pos - np.min(exon_pos))/10 + 50

        # PDFの作成
        pagesize_w = total_length + request.margin_x * 2
        pagesize_h = request.gene_h + request.margin_y * 2
        center_line_y = request.margin_y + request.gene_h/2

        page = canvas.Canvas(file_name, pagesize=(pagesize_w, pagesize_h))
        
        # 色の設定
        line_color_rgb = color_convert(request.line_color)
        exon_color_rgb = color_convert(request.exon_color)
        utr_color_rgb = color_convert(request.utr_color)
        
        page.setStrokeColorRGB(line_color_rgb[0], line_color_rgb[1], line_color_rgb[2])
        page.setFillColorRGB(exon_color_rgb[0], exon_color_rgb[1], exon_color_rgb[2])
        page.setLineWidth(1)

        # エクソンの描画
        for i in range(0, len(x), 2):
            page.rect(x[i], request.margin_y, exon_intron_length[i], request.gene_h, fill=True)

        # イントロンの描画
        if request.intron_shape == 'zigzag':
            mid_intron = []
            for i in range(1, len(x)-1, 2):
                mid = (x[i] + x[i+1])/2
                mid_intron.append(mid)

            for i, j in enumerate(range(1, len(x)-1, 2)):
                page.line(x[j], center_line_y, mid_intron[i], 0)
                page.line(mid_intron[i], 0, x[j+1], center_line_y)
        elif request.intron_shape == 'straight':
            for i in range(1, len(x)-1, 2):
                page.line(x[i], center_line_y, x[i+1], center_line_y)
        else:
            raise HTTPException(status_code=400, detail="無効なイントロン形状です")

        # UTRの描画
        page.setFillColorRGB(utr_color_rgb[0], utr_color_rgb[1], utr_color_rgb[2])

        if five_prime_UTR != 0:
            page.rect(x[0], request.margin_y, five_prime_UTR, request.gene_h, fill=True)

        if three_prime_UTR != 0:
            page.rect(x[-1]-three_prime_UTR, request.margin_y, three_prime_UTR, request.gene_h, fill=True)

        # ドメインモードの処理
        if request.mode == 'domain' and request.domains:
            for domain in request.domains:
                AA_start = domain.get('AA_start')
                AA_end = domain.get('AA_end')
                color = color_convert(domain.get('color', '#FF0000'))

                cDNA_start = (AA_start * 3)/10 + five_prime_UTR
                cDNA_end = (AA_end * 3)/10 + five_prime_UTR

                gDNA_start = cDNA_pos2gDNA_pos(cDNA_exon_pos, cDNA_start, cumsum_intron_len) + 50 
                gDNA_end = cDNA_pos2gDNA_pos(cDNA_exon_pos, cDNA_end, cumsum_intron_len) + 50

                if gDNA_end > x[-1]:
                    print(f'The end position of domain is out of range.')

                domain_pos = x[(gDNA_start <= x) & (x <= gDNA_end)]
                domain_pos = np.sort(np.append([gDNA_start, gDNA_end], domain_pos))
                domain_len = np.asarray([(domain_pos[i+1] - domain_pos[i]) for i in range(len(domain_pos)-1)])

                page.setFillColorRGB(color[0], color[1], color[2])

                for j in range(0, len(domain_len), 2):
                    page.rect(domain_pos[j], request.margin_y, domain_len[j], request.gene_h, fill=True)

        page.save()
        
        # ファイルの返却
        return FileResponse(
            file_name,
            media_type="application/pdf",
            filename=os.path.basename(file_name)
        )
        
    except Exception as e:
        print(f"遺伝子構造の生成中にエラーが発生しました: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 既存のForm処理APIエンドポイントも互換性のために残しておく場合は以下のようにする
@app.post("/api/py/generate-gene-structure-from-file")
async def generate_gene_structure_from_file(
    request: str = Form(...),
    gff_file: UploadFile = File(...)
):
    try:
        # リクエストJSONをパース
        request_data = json.loads(request)
        # GeneStructureRequestモデルに変換
        request_model = GeneStructureRequest(**request_data)
        
        # Vercel環境用の一時ディレクトリパスを設定
        temp_dir = '/tmp' if os.environ.get('VERCEL') == '1' else tempfile.gettempdir()
        
        # アップロードされたGFFファイルを一時ファイルとして保存
        temp_gff_path = os.path.join(temp_dir, f"temp_gff_{os.urandom(8).hex()}.gff3")
        
        try:
            contents = await gff_file.read()
            with open(temp_gff_path, 'wb') as f:
                f.write(contents)
        except Exception as e:
            if os.path.exists(temp_gff_path):
                os.unlink(temp_gff_path)
            raise HTTPException(status_code=400, detail=f"GFFファイルの読み込みに失敗しました: {str(e)}")
        
        # 一時ファイルの作成
        if not request_model.file_name:
            output_path = os.path.join(temp_dir, f"output_{os.urandom(8).hex()}.pdf")
            file_name = output_path
        else:
            file_name = request_model.file_name

        # トランスクリプトIDの取得
        transcript_result = get_transcript_id(temp_gff_path, request_model.gene_id)
        if not transcript_result:
            os.unlink(temp_gff_path)
            raise HTTPException(status_code=400, detail="無効なファイル形式です。.gff3ファイルのみ対応しています。")
        
        transcript_id, strand = transcript_result
        if not transcript_id:
            os.unlink(temp_gff_path)
            raise HTTPException(status_code=404, detail=f'遺伝子ID "{request_model.gene_id}" が見つかりませんでした。')

        # 遺伝子構造の取得
        total_length, exon_pos, five_prime_UTR, three_prime_UTR = get_structure(temp_gff_path, transcript_id)

        # エキソン＆イントロン長の計算
        if strand == '-':
            exon_intron_length = np.asarray([(exon_pos[i+1] - exon_pos[i])/10 for i in range(len(exon_pos)-1)])[::-1]
        else:
            exon_intron_length = np.asarray([(exon_pos[i+1] - exon_pos[i])/10 for i in range(len(exon_pos)-1)])

        exon_len = np.asarray([exon_intron_length[i] for i in range(len(exon_intron_length)) if i % 2 == 0])
        intron_len = np.asarray([exon_intron_length[i] for i in range(len(exon_intron_length)) if i % 2 == 1])

        # 累積イントロン長
        cumsum_intron_len = np.append(np.append(0, np.cumsum(intron_len)), 0)
        # cDNAでの位置
        cDNA_exon_pos = np.append(0, np.cumsum(exon_len))

        # 基本の作図用
        if strand == '-':
            x = np.abs(exon_pos - np.max(exon_pos))[::-1]/10 + 50
        else:
            x = (exon_pos - np.min(exon_pos))/10 + 50

        # PDFの作成
        pagesize_w = total_length + request_model.margin_x * 2
        pagesize_h = request_model.gene_h + request_model.margin_y * 2
        center_line_y = request_model.margin_y + request_model.gene_h/2

        page = canvas.Canvas(file_name, pagesize=(pagesize_w, pagesize_h))
        
        # 色の設定
        line_color_rgb = color_convert(request_model.line_color)
        exon_color_rgb = color_convert(request_model.exon_color)
        utr_color_rgb = color_convert(request_model.utr_color)
        
        page.setStrokeColorRGB(line_color_rgb[0], line_color_rgb[1], line_color_rgb[2])
        page.setFillColorRGB(exon_color_rgb[0], exon_color_rgb[1], exon_color_rgb[2])
        page.setLineWidth(1)

        # エクソンの描画
        for i in range(0, len(x), 2):
            page.rect(x[i], request_model.margin_y, exon_intron_length[i], request_model.gene_h, fill=True)

        # イントロンの描画
        if request_model.intron_shape == 'zigzag':
            mid_intron = []
            for i in range(1, len(x)-1, 2):
                mid = (x[i] + x[i+1])/2
                mid_intron.append(mid)

            for i, j in enumerate(range(1, len(x)-1, 2)):
                page.line(x[j], center_line_y, mid_intron[i], 0)
                page.line(mid_intron[i], 0, x[j+1], center_line_y)
        elif request_model.intron_shape == 'straight':
            for i in range(1, len(x)-1, 2):
                page.line(x[i], center_line_y, x[i+1], center_line_y)
        else:
            raise HTTPException(status_code=400, detail="Invalid intron shape")

        # UTRの描画
        page.setFillColorRGB(utr_color_rgb[0], utr_color_rgb[1], utr_color_rgb[2])

        if five_prime_UTR != 0:
            page.rect(x[0], request_model.margin_y, five_prime_UTR, request_model.gene_h, fill=True)

        if three_prime_UTR != 0:
            page.rect(x[-1]-three_prime_UTR, request_model.margin_y, three_prime_UTR, request_model.gene_h, fill=True)

        # ドメインモードの処理
        if request_model.mode == 'domain' and request_model.domains:
            for domain in request_model.domains:
                AA_start = domain.get('AA_start')
                AA_end = domain.get('AA_end')
                color = color_convert(domain.get('color', '#FF0000'))

                cDNA_start = (AA_start * 3)/10 + five_prime_UTR
                cDNA_end = (AA_end * 3)/10 + five_prime_UTR

                gDNA_start = cDNA_pos2gDNA_pos(cDNA_exon_pos, cDNA_start, cumsum_intron_len) + 50 
                gDNA_end = cDNA_pos2gDNA_pos(cDNA_exon_pos, cDNA_end, cumsum_intron_len) + 50

                if gDNA_end > x[-1]:
                    print(f'The end position of domain is out of range.')

                domain_pos = x[(gDNA_start <= x) & (x <= gDNA_end)]
                domain_pos = np.sort(np.append([gDNA_start, gDNA_end], domain_pos))
                domain_len = np.asarray([(domain_pos[i+1] - domain_pos[i]) for i in range(len(domain_pos)-1)])

                page.setFillColorRGB(color[0], color[1], color[2])

                for j in range(0, len(domain_len), 2):
                    page.rect(domain_pos[j], request_model.margin_y, domain_len[j], request_model.gene_h, fill=True)

        page.save()
        
        # 処理終了後、一時ファイルを削除
        if os.path.exists(temp_gff_path):
            os.unlink(temp_gff_path)
        
        # ファイルの返却
        return FileResponse(
            file_name,
            media_type="application/pdf",
            filename=os.path.basename(file_name)
        )
        
    except Exception as e:
        # エラーが発生した場合も一時ファイルを削除する
        if 'temp_gff_path' in locals() and os.path.exists(temp_gff_path):
            try:
                os.unlink(temp_gff_path)
            except:
                pass
        
        print(f"遺伝子構造の生成中にエラーが発生しました: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
