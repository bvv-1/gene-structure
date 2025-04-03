from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import os
from reportlab.pdfgen import canvas
import numpy as np
from pydantic import BaseModel
from typing import Optional, List
import io
import svgwrite


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
    mode: str = "basic"
    file_name: str
    utr_color: str = "#CCCCCC"
    exon_color: str = "#000000"
    line_color: str = "#000000"
    margin_x: int = 50
    margin_y: int = 50
    intron_shape: str = "straight"
    gene_h: int = 20
    domains: Optional[List[dict]] = None
    gene_structure: GeneStructureInfo

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
def health_check():
    return {"message": "Hello from FastAPI"}

@app.post("/api/py/generate-gene-structure-svg")
async def generate_gene_structure_svg(request: GeneStructureRequest):
    try:
        # 構造情報の取り出し
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

        # SVGの作成
        pagesize_w = total_length + request.margin_x * 2
        pagesize_h = request.gene_h + request.margin_y * 2
        center_line_y = request.margin_y + request.gene_h/2

        svg_io = io.StringIO()
        dwg = svgwrite.Drawing(size=(pagesize_w, pagesize_h), profile='tiny')
        
        # 色の設定
        line_color = request.line_color
        exon_color = request.exon_color
        utr_color = request.utr_color

        # エクソンの描画
        for i in range(0, len(x), 2):
            dwg.add(dwg.rect(
                insert=(x[i], request.margin_y),
                size=(exon_intron_length[i], request.gene_h),
                fill=exon_color
            ))

        # イントロンの描画
        if request.intron_shape == 'zigzag':
            mid_intron = []
            for i in range(1, len(x)-1, 2):
                mid = (x[i] + x[i+1])/2
                mid_intron.append(mid)

            for i, j in enumerate(range(1, len(x)-1, 2)):
                dwg.add(dwg.line(
                    start=(x[j], center_line_y),
                    end=(mid_intron[i], 0),
                    stroke=line_color
                ))
                dwg.add(dwg.line(
                    start=(mid_intron[i], 0),
                    end=(x[j+1], center_line_y),
                    stroke=line_color
                ))
        elif request.intron_shape == 'straight':
            for i in range(1, len(x)-1, 2):
                dwg.add(dwg.line(
                    start=(x[i], center_line_y),
                    end=(x[i+1], center_line_y),
                    stroke=line_color
                ))
        else:
            raise HTTPException(status_code=400, detail="無効なイントロン形状です")

        # UTRの描画
        if five_prime_UTR != 0:
            dwg.add(dwg.rect(
                insert=(x[0], request.margin_y),
                size=(five_prime_UTR, request.gene_h),
                fill=utr_color
            ))

        if three_prime_UTR != 0:
            dwg.add(dwg.rect(
                insert=(x[-1]-three_prime_UTR, request.margin_y),
                size=(three_prime_UTR, request.gene_h),
                fill=utr_color
            ))

        # ドメインモードの処理
        if request.mode == 'domain' and request.domains:
            for domain in request.domains:
                AA_start = domain.get('AA_start')
                AA_end = domain.get('AA_end')
                color = domain.get('color', '#FF0000')

                cDNA_start = (AA_start * 3)/10 + five_prime_UTR
                cDNA_end = (AA_end * 3)/10 + five_prime_UTR

                gDNA_start = cDNA_pos2gDNA_pos(cDNA_exon_pos, cDNA_start, cumsum_intron_len) + 50 
                gDNA_end = cDNA_pos2gDNA_pos(cDNA_exon_pos, cDNA_end, cumsum_intron_len) + 50

                if gDNA_end > x[-1]:
                    print(f'The end position of domain is out of range.')

                domain_pos = x[(gDNA_start <= x) & (x <= gDNA_end)]
                domain_pos = np.sort(np.append([gDNA_start, gDNA_end], domain_pos))
                domain_len = np.asarray([(domain_pos[i+1] - domain_pos[i]) for i in range(len(domain_pos)-1)])

                for j in range(0, len(domain_len), 2):
                    dwg.add(dwg.rect(
                        insert=(domain_pos[j], request.margin_y),
                        size=(domain_len[j], request.gene_h),
                        fill=color
                    ))

        svg_content = dwg.tostring()
        
        # SVG内容をレスポンスとして返却
        return Response(
            content=svg_content,
            media_type="image/svg+xml"
        )
        
    except Exception as e:
        print(f"SVG遺伝子構造の生成中にエラーが発生しました: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# @app.post("/api/py/generate-gene-structure-pdf")
# async def generate_gene_structure_pdf(request: GeneStructureRequest):
#     try:
#         # 構造情報の取り出し
#         strand = request.gene_structure.strand
#         total_length = request.gene_structure.total_length
#         exon_pos = request.gene_structure.exon_positions
#         five_prime_UTR = request.gene_structure.five_prime_utr
#         three_prime_UTR = request.gene_structure.three_prime_utr
#         file_name = request.file_name

#         # エキソン＆イントロン長の計算
#         if strand == '-':
#             exon_intron_length = np.asarray([(exon_pos[i+1] - exon_pos[i])/10 for i in range(len(exon_pos)-1)])[::-1]
#         else:
#             exon_intron_length = np.asarray([(exon_pos[i+1] - exon_pos[i])/10 for i in range(len(exon_pos)-1)])

#         exon_len = np.asarray([exon_intron_length[i] for i in range(len(exon_intron_length)) if i % 2 == 0])
#         intron_len = np.asarray([exon_intron_length[i] for i in range(len(exon_intron_length)) if i % 2 == 1])

#         # 累積イントロン長
#         cumsum_intron_len = np.append(np.append(0, np.cumsum(intron_len)), 0)
#         # cDNAでの位置
#         cDNA_exon_pos = np.append(0, np.cumsum(exon_len))

#         # 基本の作図用
#         if strand == '-':
#             x = np.abs(exon_pos - np.max(exon_pos))[::-1]/10 + 50
#         else:
#             x = (exon_pos - np.min(exon_pos))/10 + 50

#         # PDFの作成
#         pagesize_w = total_length + request.margin_x * 2
#         pagesize_h = request.gene_h + request.margin_y * 2
#         center_line_y = request.margin_y + request.gene_h/2

#         page = canvas.Canvas(file_name, pagesize=(pagesize_w, pagesize_h))
        
#         # 色の設定
#         line_color_rgb = color_convert(request.line_color)
#         exon_color_rgb = color_convert(request.exon_color)
#         utr_color_rgb = color_convert(request.utr_color)
        
#         page.setStrokeColorRGB(line_color_rgb[0], line_color_rgb[1], line_color_rgb[2])
#         page.setFillColorRGB(exon_color_rgb[0], exon_color_rgb[1], exon_color_rgb[2])
#         page.setLineWidth(1)

#         # エクソンの描画
#         for i in range(0, len(x), 2):
#             page.rect(x[i], request.margin_y, exon_intron_length[i], request.gene_h, fill=True)

#         # イントロンの描画
#         if request.intron_shape == 'zigzag':
#             mid_intron = []
#             for i in range(1, len(x)-1, 2):
#                 mid = (x[i] + x[i+1])/2
#                 mid_intron.append(mid)

#             for i, j in enumerate(range(1, len(x)-1, 2)):
#                 page.line(x[j], center_line_y, mid_intron[i], 0)
#                 page.line(mid_intron[i], 0, x[j+1], center_line_y)
#         elif request.intron_shape == 'straight':
#             for i in range(1, len(x)-1, 2):
#                 page.line(x[i], center_line_y, x[i+1], center_line_y)
#         else:
#             raise HTTPException(status_code=400, detail="無効なイントロン形状です")

#         # UTRの描画
#         page.setFillColorRGB(utr_color_rgb[0], utr_color_rgb[1], utr_color_rgb[2])

#         if five_prime_UTR != 0:
#             page.rect(x[0], request.margin_y, five_prime_UTR, request.gene_h, fill=True)

#         if three_prime_UTR != 0:
#             page.rect(x[-1]-three_prime_UTR, request.margin_y, three_prime_UTR, request.gene_h, fill=True)

#         # ドメインモードの処理
#         if request.mode == 'domain' and request.domains:
#             for domain in request.domains:
#                 AA_start = domain.get('AA_start')
#                 AA_end = domain.get('AA_end')
#                 color = color_convert(domain.get('color', '#FF0000'))

#                 cDNA_start = (AA_start * 3)/10 + five_prime_UTR
#                 cDNA_end = (AA_end * 3)/10 + five_prime_UTR

#                 gDNA_start = cDNA_pos2gDNA_pos(cDNA_exon_pos, cDNA_start, cumsum_intron_len) + 50 
#                 gDNA_end = cDNA_pos2gDNA_pos(cDNA_exon_pos, cDNA_end, cumsum_intron_len) + 50

#                 if gDNA_end > x[-1]:
#                     print(f'The end position of domain is out of range.')

#                 domain_pos = x[(gDNA_start <= x) & (x <= gDNA_end)]
#                 domain_pos = np.sort(np.append([gDNA_start, gDNA_end], domain_pos))
#                 domain_len = np.asarray([(domain_pos[i+1] - domain_pos[i]) for i in range(len(domain_pos)-1)])

#                 page.setFillColorRGB(color[0], color[1], color[2])

#                 for j in range(0, len(domain_len), 2):
#                     page.rect(domain_pos[j], request.margin_y, domain_len[j], request.gene_h, fill=True)

#         page.save()
        
#         # ファイルの返却
#         return FileResponse(
#             file_name,
#             media_type="application/pdf",
#             filename=os.path.basename(file_name)
#         )
        
#     except Exception as e:
#         print(f"遺伝子構造の生成中にエラーが発生しました: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))
