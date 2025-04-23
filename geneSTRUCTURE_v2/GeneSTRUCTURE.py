
import svgwrite
import re
import sys
import numpy as np
import configparser
import colorsys
from logging import getLogger, StreamHandler, FileHandler, DEBUG, INFO, WARNING, Formatter


logger = getLogger(__name__)
logger.setLevel(DEBUG)

sh = StreamHandler()
sh.setLevel(INFO)
sh.setFormatter(Formatter("%(asctime)s %(levelname)8s %(message)s"))

fh = FileHandler(filename = 'geneSTRUCTURE.log', mode = 'w')
fh.setLevel(DEBUG)
fh.setFormatter(Formatter("%(asctime)s %(levelname)8s %(message)s"))

logger.addHandler(sh)
logger.addHandler(fh)

#################################################
#   Function Definitions
#################################################


def print_welcome_message():
    part1 = """\
                             _____  _______  _____   _    _   _____  _______  _    _  _____   ______
                            / ____||__   __||  __ \\ | |  | | / ____||__   __|| |  | ||  __ \\ |  ____|"""

    part2 = """\
   __ _   ___  _ __    ___ | (___     | |   | |__) || |  | || |        | |   | |  | || |__) || |__ 
  / _` | / _ \\| '_ \\  / _ \\ \\___ \\    | |   |  _  / | |  | || |        | |   | |  | ||  _  / |  __|"""

    part3 = """\
 | (_| ||  __/| | | ||  __/ ____) |   | |   | | \\ \\ | |__| || |____    | |   | |__| || | \\ \\ | |____
  \\__, | \\___||_| |_| \\___||_____/    |_|   |_|  \\_\\ \\____/  \\_____|   |_|    \\____/ |_|  \\_\\|______|
   __/ |
  |___/  """
 

    part4 = """█████████████████████████────────────██████████████████────────────███████████"""                                                                                         
    
    yellow = "\033[33m"
    red = "\033[91m"
    green = "\033[92m"
    blue = "\033[94m"
    reset = "\033[0m"

    utr = "███████"

    intron = "───────"
    print(red + part1 + '\n' + green + part2 + '\n' + blue + part3 +  blue + utr + yellow + part4 + blue + utr + reset)

    print("------------------------------------------------------------------------------------------------------")
    print("Documentation: https://github.com/hashimotoshumpei/geneSTRUCTURE\n")
    print("Type --help for help.\n")
    print("Version 1.0.0 (2025-4-11)")
    print("------------------------------------------------------------------------------------------------------")


print_welcome_message()


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

def get_structure(transcript_id):

    mRNA_pos = []

    exon_pos = []
    #exon_len = []

    cds_pos = []
    cds_len = []

    five_prime_UTR_pos = []
    three_prime_UTR_pos = []

    five_prime_UTR_len = []
    three_prime_UTR_len = []

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

                # この書き方はやめる。"id" in line[8] でいい。
                # id_col = re.split('[:;]', line[8])
                if transcript_id in line[8]:

                    strand = line[6]

                    if line[2] == 'mRNA':
                        mRNA_pos.append(int(line[3]))
                        mRNA_pos.append(int(line[4]))
                        total_length = (int(line[4]) - int(line[3]))/10
                    elif line[2] == 'CDS':
                        exon_pos.append(int(line[3]))
                        exon_pos.append(int(line[4]))
                        cds_pos.append(int(line[3]))
                        cds_pos.append(int(line[4]))
                        cds_len.append((int(line[4]) - int(line[3]))/10)
                    elif line[2] == 'five_prime_UTR':
                        exon_pos.append(int(line[3]))
                        exon_pos.append(int(line[4]))
                        five_prime_UTR_pos.append(int(line[3]))
                        five_prime_UTR_pos.append(int(line[4]))
                        five_prime_UTR_len.append((int(line[4]) - int(line[3]))/10)
                        five_prime_UTR = (int(line[4]) - int(line[3]))/10
                    elif line[2] == 'three_prime_UTR':
                        exon_pos.append(int(line[3]))
                        exon_pos.append(int(line[4]))
                        three_prime_UTR_pos.append(int(line[3]))
                        three_prime_UTR_pos.append(int(line[4]))
                        three_prime_UTR_len.append((int(line[4]) - int(line[3]))/10)
                        three_prime_UTR = (int(line[4]) - int(line[3]))/10

        if strand == '+':
            mRNA_pos = np.array(mRNA_pos)
            exon_pos = np.array(exon_pos)
            cds_pos = np.array(cds_pos)
            five_prime_UTR_pos = np.array(five_prime_UTR_pos)
            three_prime_UTR_pos = np.array(three_prime_UTR_pos)
        
        if strand == '-':
            mRNA_pos = np.array(mRNA_pos) * -1
            exon_pos = np.array(exon_pos) * -1
            cds_pos = np.array(cds_pos) * -1
            five_prime_UTR_pos = np.array(five_prime_UTR_pos) * -1
            three_prime_UTR_pos = np.array(three_prime_UTR_pos) * -1
    
    return total_length, mRNA_pos, exon_pos, cds_pos, five_prime_UTR_pos, three_prime_UTR_pos, five_prime_UTR, three_prime_UTR, strand

def cDNA_pos2gDNA_pos(cDNA_exon_pos, domain_cDNA_pos):
    print('domain_cDNA_pos:', domain_cDNA_pos)
    print('cDNA_exon_pos:', cDNA_exon_pos)
    x2 = np.sort(np.append(cDNA_exon_pos, domain_cDNA_pos))
    index = int(np.where(x2 == domain_cDNA_pos)[0])
    print('index:', index)
    gDNA_pos = domain_cDNA_pos + cumsum_intron_len[index-1]
    print('cumsum_intron_len[index-1]:', cumsum_intron_len[index-1])

    return gDNA_pos

# deletion の両端が exon 内に含まれていなければ exon_pos に追加
def is_position_in_exon(exon_pos, pos):
    print("exon_pos", len(exon_pos))
    for i in range(0, len(exon_pos), 2):
        if exon_pos[i] <= pos <= exon_pos[i+1]:
            return True
    return False


def update_exon_positions_with_deletion(exon_pos, del_pos):
    del_pos = del_pos + np.min(cds_pos)
    del_start, del_end = del_pos[0], del_pos[1]

    is_del_end_in_exon = True
    is_del_start_in_exon = True

    if not is_position_in_exon(exon_pos, del_end):
        exon_pos = np.append(exon_pos, del_end)
        is_del_end_in_exon = False

    if not is_position_in_exon(exon_pos, del_start):
        exon_pos = np.append(exon_pos, del_start)
        is_del_start_in_exon = False

    # deletion の開始・終了点も exon_pos に追加
    exon_pos = np.append(exon_pos, del_pos)

    # ソートして deletion 範囲内の部分を除去
    exon_pos.sort()
    updated_exon_pos = exon_pos[(exon_pos <= del_start) | (exon_pos >= del_end)]

    return updated_exon_pos, is_del_start_in_exon, is_del_end_in_exon
    
###################################################
# config settings
###################################################

inifile = configparser.ConfigParser()
inifile.read('./config.ini')

mode = inifile.get('mode_setting', 'mode')
mode = 'domain'
# file settings
gff_path = inifile.get('file_settings', 'gff_path')
transcript_id = inifile.get('file_settings', 'transcript_id')
file_name = inifile.get('file_settings', 'file_name')

# color setting
utr_color = inifile.get('color_settings', 'UTR_color')
exon_color = inifile.get('color_settings', 'Exon_color')
line_color = inifile.get('color_settings', 'line_color')

# gradation setting
utr_gradation = inifile.get('gradation_settings', 'UTR_gradation') # on or off 
exon_gradation = inifile.get('gradation_settings', 'Exon_gradation') # on or off

# drawing_settings
deletion_shape = inifile.get('drawing_settings', 'deletion_shape') # dashed or zigzag
stroke = inifile.get('drawing_settings', 'stroke') # on or off

# 自動的に決まるようにする！！　か、デフォルトで適当に決めるか・・・
# drawing settings
margin_x = int(inifile.get('drawing_settings', 'margin_x'))
margin_y = int(inifile.get('drawing_settings', 'margin_y'))
gene_h = int(inifile.get('drawing_settings', 'gene_h'))

##################################### main script ############################################ 

total_length, mRNA_pos, exon_pos, cds_pos, five_prime_UTR_pos, three_prime_UTR_pos, five_prime_UTR, three_prime_UTR, strand = get_structure(transcript_id)

print('#################')
print('total_length:', total_length)
print('exon_pos:', exon_pos)
print('cds_pos:', cds_pos)
print('five_prime_UTR:', five_prime_UTR)
print('three_prime_UTR:', three_prime_UTR)
print('#################')

if not get_structure(transcript_id):
    logger.info(f'Gene ID "{gene_id}" was not found.')
    sys.exit()

if five_prime_UTR == 0:
    logger.info("There was no annotation for 5'UTR")

if three_prime_UTR == 0:
    logger.info("There was no annotation for 3'UTR")

# ここに必要？
exon_pos = np.array(exon_pos)
exon_pos = np.sort(exon_pos)
cds_pos = np.array(cds_pos)
cds_pos = np.sort(cds_pos)
#################

del_pos = np.array([1, 100])



######################################
# 計算
######################################


#ドメイン構造は、deletionで更新する前の exon_pos を使って、ドメインのstart endを決める。




# ひとまず、deletionは無視！！
exon_pos, is_del_start_in_exon, is_del_end_in_exon = update_exon_positions_with_deletion(exon_pos, del_pos)

#エキソン＆イントロン長を取得
exon_intron_length = np.asarray([(exon_pos[i+1] - exon_pos[i])/10 for i in range(len(exon_pos)-1)])

exon_len = np.asarray([exon_intron_length[i] for i in range(len(exon_intron_length)) if i % 2 == 0])
intron_len = np.asarray([exon_intron_length[i] for i in range(len(exon_intron_length)) if i % 2 == 1])
print('exon_len:', exon_len)

# 累積イントロン長
cumsum_intron_len = np.append(np.append(0, np.cumsum(intron_len)), 0)
print('cumsum_intron_len:', cumsum_intron_len)
# cDNAでの位置
cDNA_exon_pos = np.append(0, np.cumsum(exon_len)) + 50
x  = (exon_pos - np.min(cds_pos))/10 + 50
cds_pos = (cds_pos - np.min(cds_pos))/10 + 50

######################################
# Printing Settings
######################################

pagesize_w = total_length + margin_x * 2
pagesize_h = gene_h + margin_y * 2
center_line_y = margin_y + gene_h/2

# SVGファイルの作成
file_name = "gene_structure.svg"
dwg = svgwrite.Drawing(filename=file_name, size=(pagesize_w, pagesize_h))

grad_dict = {}

if utr_gradation == "on":
    utr_color = f'url(#{get_or_create_gradient(dwg, utr_color, grad_dict)})'

if exon_gradation == "on":
    exon_color = f'url(#{get_or_create_gradient(dwg, exon_color, grad_dict)})'

stroke_width = 1


stroke = "on"
deletion_flag = del_pos[0]/10 + 50

######################################
# Exon の描画
######################################

for i in range(0, len(x), 2):
    dwg.add(dwg.rect(
        insert=(x[i], margin_y),
        size=(exon_intron_length[i], gene_h),
        fill=exon_color,
        stroke="none" if stroke == "off" else line_color,
        stroke_width=stroke_width
    ))

######################################
# Intron の描画
######################################

for i in range(1, len(x) - 1, 2):
    if x[i] == deletion_flag: pass
    else:
        dwg.add(dwg.line(
            start=(x[i], center_line_y),
            end=(x[i + 1], center_line_y),
            stroke=line_color,
            stroke_width=stroke_width
        ))

######################################
# UTR の描画
######################################

five_prime_UTR = x[x < np.min(cds_pos)]

for i in range(0, len(five_prime_UTR), 2):
    dwg.add(dwg.rect(
        insert=(five_prime_UTR[i], margin_y),
        size=(exon_intron_length[i], gene_h),
        fill=utr_color,
        stroke="none" if stroke == "off" else line_color,
        stroke_width=stroke_width
    ))

three_prime_UTR = x[x > np.max(cds_pos)]
three_prime_UTR_length = np.asarray([(three_prime_UTR[i+1] - three_prime_UTR[i]) for i in range(len(three_prime_UTR)-1)])


for i in range(0, len(three_prime_UTR), 2):
    if i == len(three_prime_UTR) - 2:
        x0 = three_prime_UTR[i]       # 左端
        x1 = three_prime_UTR[i+1]     # 右端
        x2 = x1 + 10               # 矢印先端

        y0 = margin_y                 # 上端
        y1 = margin_y + gene_h        # 下端

        # 順序: 左上→左下→右下→右上→矢印先端（中央）
        dwg.add(dwg.polygon(
            points=[
                (x0, y0),
                (x0, y1),
                (x1, y1),
                (x2, center_line_y),
                (x1, y0)
            ],
            fill=utr_color,
            stroke="none" if stroke == "off" else line_color,
            stroke_width=stroke_width
        ))

    else:
        dwg.add(dwg.rect(
            insert=(three_prime_UTR[i], margin_y),
            size=(three_prime_UTR_length[i], gene_h),
            fill=utr_color,
            # fill=exon_fill,
            stroke="none" if stroke == "off" else line_color,
            stroke_width=stroke_width
        ))

######################################
# Deletionの描画
######################################


for i in range(1, len(x) - 1, 2):
    if x[i] == deletion_flag:
        if deletion_shape == 'zigzag':

            y1 = center_line_y
            y2 = margin_y
            y3 = center_line_y

            if is_del_start_in_exon:
                y1 = center_line_y - gene_h/2
                y2 = margin_y - gene_h/2

            if is_del_end_in_exon:
                y3 = center_line_y - gene_h/2
                y2 = margin_y - gene_h/2

            points = [
                (x[i], y1),
                ((x[i+1]+x[i])/2, y2),
                (x[i + 1], y3)
            ]
            dwg.add(dwg.polyline(
                points=points,
                stroke=line_color,
                stroke_width=stroke_width,
                fill="none"
            ))

        if deletion_shape == 'dashed':
            dwg.add(dwg.line(
                start=(x[i], center_line_y),
                end=(x[i + 1], center_line_y),
                stroke=line_color,
                stroke_width=stroke_width,
                style='stroke-dasharray:5,1'
            ))

######################################
# Insertionの描画
######################################

ins_pos = np.array([2000, 6])
ins_pos_x = int(ins_pos[0]/10 + 50)

add_len = 10
triangle_w = 30
triangle_h = 10
line_upper_y = int(margin_y - add_len)
line_lower_y = int(margin_y + gene_h + add_len)

dwg.add(dwg.line(
                start=(ins_pos_x, line_upper_y),
                end=(ins_pos_x, line_lower_y),
                stroke=line_color,
                stroke_width=stroke_width
            ))

points = [
    (ins_pos_x, line_upper_y),
    (ins_pos_x - triangle_w/2, line_upper_y - triangle_h),
    (ins_pos_x + triangle_w/2, line_upper_y - triangle_h)
    ]

triangle = dwg.polygon(
    points=points,
    fill='black',
    stroke='black',
    stroke_width=2
)

dwg.add(triangle)




###########################################
# Domain mode
###########################################

if mode == 'domain':

    n_domain = int(inifile.get('domain_settings', 'number_of_domains'))

    for i in range(n_domain):

        AA_start = int(inifile.get('domain_settings', f'domain{i+1}_AA_start'))
        AA_end = int(inifile.get('domain_settings', f'domain{i+1}_AA_end'))
        color = inifile.get('color_settings', f'domain{i+1}_color')

        if exon_gradation == "on":
            color = f'url(#{get_or_create_gradient(dwg, color, grad_dict)})'

        cDNA_start = (AA_start * 3)/10 + 50
        cDNA_end = (AA_end * 3)/10 + 50

        print('cDNA_start:', cDNA_start)
        print('cDNA_end:', cDNA_end)

        gDNA_start = cDNA_pos2gDNA_pos(cDNA_exon_pos, cDNA_start) 
        gDNA_end = cDNA_pos2gDNA_pos(cDNA_exon_pos, cDNA_end) 



        if gDNA_end > x[-1]:
            logger.warning(f'The end position of domain{i+1} is out of range.') 
        # Even in this case, the end point of the domain is as same as that of codeing region.

        gDNA_start = 100 
        gDNA_end = 200
        print('511_x:', x)
        print('gDNA_start:', gDNA_start)
        print('gDNA_end:', gDNA_end)
        domain_pos = x[(gDNA_start <= x) & (x <= gDNA_end)]
        print('517_domain_pos:', domain_pos)

        print('518', is_position_in_exon(x, gDNA_start), is_position_in_exon(x, gDNA_end))
        if is_position_in_exon(x, gDNA_start) and is_position_in_exon(x, gDNA_end):
            domain_pos = np.sort(np.append([gDNA_start, gDNA_end], domain_pos))

        if not is_position_in_exon(x, gDNA_start) and is_position_in_exon(x, gDNA_end):
            domain_pos = np.sort(np.append([gDNA_end], domain_pos))
        
        if is_position_in_exon(x, gDNA_start) and not is_position_in_exon(x, gDNA_end):
            domain_pos = np.sort(np.append([gDNA_start], domain_pos))
        
        if not is_position_in_exon(x, gDNA_start) and not is_position_in_exon(x, gDNA_end):
            pass
            

        domain_len = np.asarray([(domain_pos[i+1] - domain_pos[i]) for i in range(len(domain_pos)-1)])
        print('domain_pos:', domain_pos)
        print('domain_len:', domain_len)

        for j in range(0,len(domain_len),2):
            dwg.add(dwg.rect(
                insert=(domain_pos[j], margin_y),
                size=(domain_len[j], gene_h),
                fill=color,
                # fill=exon_fill,
                stroke="none" if stroke == "off" else line_color,
                stroke_width=stroke_width
            ))

dwg.add(dwg.text(
    transcript_id,
    insert=(-150, center_line_y),  # ← 右端を x=50、ベースラインを y=80 に合わせたい
    text_anchor="end",  # ← 右寄せにする
    style="dominant-baseline:middle", 
    font_size="14px"
))

dwg.viewbox(-300, 0, 1200, 100)
# SVG を保存
dwg.save()

logger.info(f'Gene structure was successfully saved as "{file_name}"')




