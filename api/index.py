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
import colorsys


### Create FastAPI instance with custom docs and openapi url
app = FastAPI(docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")

class Position(BaseModel):
    start: int
    end: int

# 遺伝子構造情報のモデルを追加
class GeneStructureInfo(BaseModel):
    transcript_id: str
    strand: str
    total_length: int
    exons: List[Position]
    cds: List[Position]
    five_prime_utrs: List[Position]
    three_prime_utrs: List[Position]
    start: int
    end: int

# リクエストモデルの定義を更新
class GeneStructureRequest(BaseModel):
    mode: str
    # file_name: str
    # utr_color: str = "#CCCCCC"
    # exon_color: str = "#000000"
    # line_color: str = "#000000"
    # margin_x: int = 50
    # margin_y: int = 50
    # intron_shape: str = "straight"
    # gene_h: int = 20
    # domains: Optional[List[dict]] = None
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

def lighten_color(hex_color, factor):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    l = min(1.0, l + factor * (1.0 - l))
    r_new, g_new, b_new = colorsys.hls_to_rgb(h, l, s)
    return '#{:02x}{:02x}{:02x}'.format(int(r_new * 255), int(g_new * 255), int(b_new * 255))


def get_or_create_gradient(dwg, base_color, grad_dict):
    if base_color in grad_dict:
        return grad_dict[base_color]

    grad_id = f'grad_{len(grad_dict)}'
    light_color = lighten_color(base_color, 0.4)
    lighter_color = lighten_color(base_color, 0.7)

    grad = dwg.linearGradient(start=('0%', '100%'), end=('0%', '0%'), id=grad_id)
    grad.add_stop_color(offset='0.0', color=base_color)
    grad.add_stop_color(offset='0.5', color=light_color)
    grad.add_stop_color(offset='1.0', color=lighter_color)
    dwg.defs.add(grad)

    grad_dict[base_color] = grad_id
    return grad_id

# deletion の両端が exon 内に含まれていなければ exon_pos に追加
def is_position_in_exon(exon_pos, pos):
    print("exon_pos", len(exon_pos))
    for i in range(0, len(exon_pos), 2):
        if exon_pos[i] <= pos <= exon_pos[i+1]:
            return True
    return False

# def update_exon_positions_with_deletion(exon_pos, del_pos, cds_pos):
#     del_pos = del_pos + np.min(cds_pos)
#     del_start, del_end = del_pos[0], del_pos[1]

#     is_del_end_in_exon = True
#     is_del_start_in_exon = True

#     if not is_position_in_exon(exon_pos, del_end):
#         exon_pos = np.append(exon_pos, del_end)
#         is_del_end_in_exon = False

#     if not is_position_in_exon(exon_pos, del_start):
#         exon_pos = np.append(exon_pos, del_start)
#         is_del_start_in_exon = False

#     # deletion の開始・終了点も exon_pos に追加
#     exon_pos = np.append(exon_pos, del_pos)

#     # ソートして deletion 範囲内の部分を除去
#     exon_pos.sort()
#     updated_exon_pos = exon_pos[(exon_pos <= del_start) | (exon_pos >= del_end)]

#     return updated_exon_pos, is_del_start_in_exon, is_del_end_in_exon
    

@app.post("/api/py/generate-gene-structure-svg")
async def generate_gene_structure_svg(request: GeneStructureRequest):
    try:
        # 構造情報の取り出し
        strand = request.gene_structure.strand
        total_length = request.gene_structure.total_length
        del_pos = np.array([1, 100])

        # exons or cds_posが空ではない
        if not request.gene_structure.exons and not request.gene_structure.cds:
            raise HTTPException(status_code=400, detail="No exons or cds positions provided.")
        if not request.gene_structure.cds:
            raise HTTPException(status_code=400, detail="Not implemented")

        min_pos = min(request.gene_structure.start, request.gene_structure.end)
        if strand == '+':
            exon_pos = [Position(start=pos.start - min_pos, end=pos.end - min_pos) for pos in request.gene_structure.exons]
            cds_pos = [Position(start=pos.start - min_pos, end=pos.end - min_pos) for pos in request.gene_structure.cds]
            five_prime_UTR = [Position(start=pos.start - min_pos, end=pos.end - min_pos) for pos in request.gene_structure.five_prime_utrs]
            three_prime_UTR = [Position(start=pos.start - min_pos, end=pos.end - min_pos) for pos in request.gene_structure.three_prime_utrs]
        else:
            exon_pos = [Position(start=pos.end - min_pos, end=pos.start - min_pos) for pos in request.gene_structure.exons]
            cds_pos = [Position(start=pos.end - min_pos, end=pos.start - min_pos) for pos in request.gene_structure.cds]
            five_prime_UTR = [Position(start=pos.end - min_pos, end=pos.start - min_pos) for pos in request.gene_structure.five_prime_utrs]
            three_prime_UTR = [Position(start=pos.end - min_pos, end=pos.start - min_pos) for pos in request.gene_structure.three_prime_utrs]
        # start < endになっているか確認
        assert all(pos.start < pos.end for pos in exon_pos), "Exon positions must have start < end"
        assert all(pos.start < pos.end for pos in cds_pos), "CDS positions must have start < end"
        assert all(pos.start < pos.end for pos in five_prime_UTR), "5' UTR positions must have start < end"
        assert all(pos.start < pos.end for pos in three_prime_UTR), "3' UTR positions must have start < end"

        # exon_pos, is_del_start_in_exon, is_del_end_in_exon = update_exon_positions_with_deletion(exon_pos, del_pos, exon_pos)
        is_del_start_in_exon = False
        is_del_end_in_exon = False

        # エキソン＆イントロン長の計算
        # if strand == '-':
        #     exon_intron_length = np.array([(exon_pos[i+1] - exon_pos[i])/10 for i in range(len(exon_pos)-1)])[::-1]
        # else:
        #     exon_intron_length = np.array([(exon_pos[i+1] - exon_pos[i])/10 for i in range(len(exon_pos)-1)])

        # exon_len = np.array([exon_intron_length[i] for i in range(len(exon_intron_length)) if i % 2 == 0])
        # intron_len = np.asarray([exon_intron_length[i] for i in range(len(exon_intron_length)) if i % 2 == 1])

        # 累積イントロン長
        # cumsum_intron_len = np.append(np.append(0, np.cumsum(intron_len)), 0)
        # cDNAでの位置
        # cDNA_exon_pos = np.append(0, np.cumsum(exon_len))

        # # 基本の作図用
        # if strand == '-':
        #     x = np.abs(exon_pos - np.max(exon_pos))[::-1]/10 + 50
        # else:
        #     x = (exon_pos - np.min(exon_pos))/10 + 50

        # SVGの作成
        margin_x = 50
        margin_y = 100
        gene_h = 20
        center_line_y = margin_y + gene_h / 2
        mode = request.mode
        utr_gradation = "on"
        exon_gradation = "on"
        exon_color = "#0077cc"
        utr_color = "#d3d3d3"
        line_color = "#000000"
        line_color = "#000000"
        deletion_shape = "zigzag"

        dwg = svgwrite.Drawing(
            size=(total_length/10 + margin_x * 2, gene_h + margin_y * 2),
            profile='tiny',
        )
        
        # grad_dict = {}

        # if utr_gradation == "on":
        #     utr_color = f'url(#{get_or_create_gradient(dwg, utr_color, grad_dict)})'

        # if exon_gradation == "on":
        #     exon_color = f'url(#{get_or_create_gradient(dwg, exon_color, grad_dict)})'

        stroke_width = 1
        stroke = "on"

        # deletion_flag = del_pos[0]/10 + 50

        ######################################
        # Exon の描画
        ######################################

        for pos in cds_pos:
            dwg.add(dwg.rect(
                insert=(pos.start/10 + margin_x, margin_y),
                size=(np.abs(pos.end-pos.start+1) / 10, gene_h),
                fill=exon_color,
                stroke="none" if stroke == "off" else line_color,
                stroke_width=stroke_width,
            ))

        # for i in range(0, len(x), 2):
        #     dwg.add(
        #         dwg.rect(
        #             insert=(x[i], margin_y),
        #             size=(exon_intron_length[i], gene_h),
        #             fill=exon_color,
        #             stroke="none" if stroke == "off" else line_color,
        #             stroke_width=stroke_width
        #         )
        #     )

        ######################################
        # UTR の描画
        ######################################

        for pos in five_prime_UTR:
            dwg.add(dwg.rect(
                insert=(pos.start/10 + margin_x, margin_y),
                size=(np.abs(pos.end-pos.start+1) / 10, gene_h),
                fill=utr_color,
                stroke="none" if stroke == "off" else line_color,
                stroke_width=stroke_width
            ))
        
        for pos in three_prime_UTR:
            dwg.add(dwg.rect(
                insert=(pos.start/10 + margin_x, margin_y),
                size=(np.abs(pos.end-pos.start+1) / 10, gene_h),
                fill=utr_color,
                stroke="none" if stroke == "off" else line_color,
                stroke_width=stroke_width
            ))

        # # five_prime_UTR = x[x < np.min(cds_pos)]

        # for i in range(0, len(five_prime_UTR), 2):
        #     dwg.add(dwg.rect(
        #         insert=(five_prime_UTR[i], margin_y),
        #         size=(exon_intron_length[i], gene_h),
        #         fill=utr_color,
        #         stroke="none" if stroke == "off" else line_color,
        #         stroke_width=stroke_width
        #     ))

        # # three_prime_UTR = x[x > np.max(cds_pos)]
        # three_prime_UTR_length = np.asarray([(three_prime_UTR[i+1] - three_prime_UTR[i]) for i in range(len(three_prime_UTR)-1)])


        # for i in range(0, len(three_prime_UTR), 2):
        #     if i == len(three_prime_UTR) - 2:
        #         x0 = three_prime_UTR[i]       # 左端
        #         x1 = three_prime_UTR[i+1]     # 右端
        #         x2 = x1 + 10               # 矢印先端

        #         y0 = margin_y                 # 上端
        #         y1 = margin_y + gene_h        # 下端

        #         # 順序: 左上→左下→右下→右上→矢印先端（中央）
        #         dwg.add(dwg.polygon(
        #             points=[
        #                 (x0, y0),
        #                 (x0, y1),
        #                 (x1, y1),
        #                 (x2, center_line_y),
        #                 (x1, y0)
        #             ],
        #             fill=utr_color,
        #             stroke="none" if stroke == "off" else line_color,
        #             stroke_width=stroke_width
        #         ))

        #     else:
        #         dwg.add(dwg.rect(
        #             insert=(three_prime_UTR[i], margin_y),
        #             size=(three_prime_UTR_length[i], gene_h),
        #             fill=utr_color,
        #             # fill=exon_fill,
        #             stroke="none" if stroke == "off" else line_color,
        #             stroke_width=stroke_width
        #         ))

        ######################################
        # Intron の描画
        ######################################

        all_positions = cds_pos + five_prime_UTR + three_prime_UTR
        all_positions.sort(key=lambda pos: pos.end)
        for i in range(0, len(all_positions) - 1):
            pos1 = all_positions[i]
            pos2 = all_positions[i + 1]
            dwg.add(dwg.line(
                start=(pos1.end/10 + margin_x, center_line_y),
                end=(pos2.start/10 + margin_x, center_line_y),
                stroke=line_color,
                stroke_width=stroke_width,
            ))


        ######################################
        # 最後を矢印状にする
        ######################################


        # ######################################
        # # Deletionの描画
        # ######################################


        # for i in range(1, len(x) - 1, 2):
        #     if x[i] == deletion_flag:
        #         if deletion_shape == 'zigzag':

        #             y1 = center_line_y
        #             y2 = margin_y
        #             y3 = center_line_y

        #             if is_del_start_in_exon:
        #                 y1 = center_line_y - gene_h/2
        #                 y2 = margin_y - gene_h/2

        #             if is_del_end_in_exon:
        #                 y3 = center_line_y - gene_h/2
        #                 y2 = margin_y - gene_h/2

        #             points = [
        #                 (x[i], y1),
        #                 ((x[i+1]+x[i])/2, y2),
        #                 (x[i + 1], y3)
        #             ]
        #             dwg.add(dwg.polyline(
        #                 points=points,
        #                 stroke=line_color,
        #                 stroke_width=stroke_width,
        #                 fill="none"
        #             ))

        #         if deletion_shape == 'dashed':
        #             dwg.add(dwg.line(
        #                 start=(x[i], center_line_y),
        #                 end=(x[i + 1], center_line_y),
        #                 stroke=line_color,
        #                 stroke_width=stroke_width,
        #                 style='stroke-dasharray:5,1'
        #             ))

        # ######################################
        # # Insertionの描画
        # ######################################

        # ins_pos = np.array([2000, 6])
        # ins_pos_x = int(ins_pos[0]/10 + 50)

        # add_len = 10
        # triangle_w = 30
        # triangle_h = 10
        # line_upper_y = int(margin_y - add_len)
        # line_lower_y = int(margin_y + gene_h + add_len)

        # dwg.add(
        #     dwg.line(
        #         start=(ins_pos_x, line_upper_y),
        #         end=(ins_pos_x, line_lower_y),
        #         stroke=line_color,
        #         stroke_width=stroke_width
        #     )
        # )

        # points = [
        #     (ins_pos_x, line_upper_y),
        #     (ins_pos_x - triangle_w/2, line_upper_y - triangle_h),
        #     (ins_pos_x + triangle_w/2, line_upper_y - triangle_h)
        # ]

        # triangle = dwg.polygon(
        #     points=points,
        #     fill='black',
        #     stroke='black',
        #     stroke_width=2
        # )

        # dwg.add(triangle)




        # ###########################################
        # # Domain mode
        # ###########################################

        # if mode == 'domain':

        #     n_domain = 1 # int(inifile.get('domain_settings', 'number_of_domains'))

        #     for i in range(n_domain):

        #         AA_start = 1 # int(inifile.get('domain_settings', f'domain{i+1}_AA_start'))
        #         AA_end = 50 # int(inifile.get('domain_settings', f'domain{i+1}_AA_end'))
        #         color = "#FAE53F" # inifile.get('color_settings', f'domain{i+1}_color')

        #         if exon_gradation == "on":
        #             color = f'url(#{get_or_create_gradient(dwg, color, grad_dict)})'

        #         cDNA_start = (AA_start * 3)/10 + 50
        #         cDNA_end = (AA_end * 3)/10 + 50

        #         print('cDNA_start:', cDNA_start)
        #         print('cDNA_end:', cDNA_end)

        #         gDNA_start = cDNA_pos2gDNA_pos(cDNA_exon_pos, cDNA_start) 
        #         gDNA_end = cDNA_pos2gDNA_pos(cDNA_exon_pos, cDNA_end) 



        #         if gDNA_end > x[-1]:
        #             print(f'The end position of domain{i+1} is out of range.') 
        #         # Even in this case, the end point of the domain is as same as that of codeing region.

        #         gDNA_start = 100 
        #         gDNA_end = 200
        #         print('511_x:', x)
        #         print('gDNA_start:', gDNA_start)
        #         print('gDNA_end:', gDNA_end)
        #         domain_pos = x[(gDNA_start <= x) & (x <= gDNA_end)]
        #         print('517_domain_pos:', domain_pos)

        #         print('518', is_position_in_exon(x, gDNA_start), is_position_in_exon(x, gDNA_end))
        #         if is_position_in_exon(x, gDNA_start) and is_position_in_exon(x, gDNA_end):
        #             domain_pos = np.sort(np.append([gDNA_start, gDNA_end], domain_pos))

        #         if not is_position_in_exon(x, gDNA_start) and is_position_in_exon(x, gDNA_end):
        #             domain_pos = np.sort(np.append([gDNA_end], domain_pos))
                
        #         if is_position_in_exon(x, gDNA_start) and not is_position_in_exon(x, gDNA_end):
        #             domain_pos = np.sort(np.append([gDNA_start], domain_pos))
                
        #         if not is_position_in_exon(x, gDNA_start) and not is_position_in_exon(x, gDNA_end):
        #             pass
                    

        #         domain_len = np.asarray([(domain_pos[i+1] - domain_pos[i]) for i in range(len(domain_pos)-1)])
        #         print('domain_pos:', domain_pos)
        #         print('domain_len:', domain_len)

        #         for j in range(0,len(domain_len),2):
        #             dwg.add(dwg.rect(
        #                 insert=(domain_pos[j], margin_y),
        #                 size=(domain_len[j], gene_h),
        #                 fill=color,
        #                 # fill=exon_fill,
        #                 stroke="none" if stroke == "off" else line_color,
        #                 stroke_width=stroke_width
        #             ))

        # dwg.add(
        #     dwg.text(
        #         "transcript_id",
        #         insert=(-150, center_line_y),  # ← 右端を x=50、ベースラインを y=80 に合わせたい
        #         text_anchor="end",  # ← 右寄せにする
        #         style="dominant-baseline:middle", 
        #         font_size="14px"
        #     )
        # )


        svg_content = dwg.tostring()
        
        # SVG内容をレスポンスとして返却
        return Response(
            content=svg_content,
            media_type="image/svg+xml"
        )
        
    except Exception as e:
        print(f"SVG遺伝子構造の生成中にエラーが発生しました: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
