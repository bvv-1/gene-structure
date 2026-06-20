import io
import math
import svgwrite
from typing import List

from .models import GeneStructure

# =====================
# 描画の色やスタイル設定
# =====================

DEFAULT_COLORS = {
    'utr_color': 'orange',
    'exon_color': 'lightblue',
    'line_color': 'black',
    'domain_color': 'green',
}

FEATURE_OUTLINES = {
    'exon': 'black',
    'CDS': 'black',
    'five_prime_UTR': 'black',
    'three_prime_UTR': 'black',
    'domain': 'black',
}

FEATURE_OUTLINE_ENABLED = {
    'exon': True,
    'CDS': True,
    'five_prime_UTR': True,
    'three_prime_UTR': True,
    'domain': True,
}

FEATURE_OUTLINE_WIDTHS = {
    'exon': 1,
    'CDS': 1,
    'five_prime_UTR': 1,
    'three_prime_UTR': 1,
    'domain': 1,
    'intron': 1,
}

LEFT_MARGIN = 50  # 左側マージン


# =====================
# ヘルパー関数
# =====================

def get_insertion_base_width(length_bp: int, shrink_factor: float, scale: float) -> float:
    """
    挿入の長さに応じて逆三角形の底辺幅を計算

    Args:
        length_bp: 挿入の長さ（bp）
        shrink_factor: 座標の縮小係数
        scale: スケール倍率

    Returns:
        底辺幅（ピクセル）
    """
    # 実際のbp長をスケール変換
    scaled_width = (length_bp / shrink_factor) * scale

    # 最小幅と最大幅を設定
    min_width = 8
    max_width = 40

    return max(min_width, min(scaled_width, max_width))

def get_baseline_segments(actual_min_start: int, actual_max_end: int, deletion_regions: List[any]) -> List[tuple]:
    """
    全体の開始・終了座標とデリーション領域を基に、
    デリーションを避けたベースラインのセグメントリストを返す
    """
    if actual_min_start >= actual_max_end:
        return []
    
    segments = [(actual_min_start, actual_max_end)]
    
    for deletion in deletion_regions:
        # deletionは api/models.Deletion オブジェクトか、geneSTRUCTUREのdict
        if hasattr(deletion, 'start'):
            del_start, del_end = deletion.start, deletion.end
        elif isinstance(deletion, dict):
            del_start, del_end = deletion['start'], deletion['end']
        else:
            del_start, del_end = deletion
            
        new_segments = []
        for seg_start, seg_end in segments:
            if seg_end < del_start or seg_start > del_end:
                new_segments.append((seg_start, seg_end))
            else:
                if seg_start < del_start:
                    new_segments.append((seg_start, del_start - 1))
                if seg_end > del_end:
                    new_segments.append((del_end + 1, seg_end))
        segments = new_segments
        
    return [s for s in segments if s[0] < s[1]]

def get_structural_extent(gene: GeneStructure) -> tuple:
    """
    遺伝子本体を構成するフィーチャーだけから開始・終了座標を返す。
    domain や variant は遺伝子外に置かれることがあるため、ベースラインの範囲には使わない。
    """
    structural_types = {'exon', 'CDS', 'five_prime_UTR', 'three_prime_UTR', 'intron'}
    structural_features = [
        f for f in gene.features
        if f.feature_type in structural_types
    ]

    if not structural_features:
        return gene.get_full_extent()

    return (
        min(f.start for f in structural_features),
        max(f.end for f in structural_features),
    )

def get_tick_params(range_size: int, shrink_factor: float = 30.0, scale: float = 2.0) -> tuple:
    """
    範囲サイズと物理的なスケールに応じて、重なり合わない適切な目盛り間隔と単位を返す
    """
    # 目標とする最小ピクセル間隔（ラベルが重ならないように）
    min_pixel_step = 50 
    # 最小ピクセル間隔を bp に換算
    min_bp_step = min_pixel_step * shrink_factor / scale
    
    # 小さな範囲でも最低限の目盛りが出るように調整
    if range_size <= 0:
        return 1, "bp", 1

    # 1, 2, 5 の倍数の中から、min_bp_step に近い適切な値を探す
    exponent = math.floor(math.log10(min_bp_step))
    magnitude = 10 ** exponent
    
    candidates = [1 * magnitude, 2 * magnitude, 5 * magnitude, 10 * magnitude]
    step = 10 * magnitude
    for c in candidates:
        if c >= min_bp_step:
            step = c
            break
    
    # 範囲に対して目盛りが少なすぎる（3個未満）場合は、一段階細かいステップを検討
    # ただし、ラベルの重なりを避けるため最小ピクセル間隔は下回らない
    if range_size / step < 2.5 and step / 2 >= min_bp_step:
        if step == 10 * magnitude: step = 5 * magnitude
        elif step == 5 * magnitude: step = 2 * magnitude
        elif step == 2 * magnitude: step = 1 * magnitude
        else: step = magnitude / 2
            
    step = int(step) if step >= 1 else 1
    
    # 単位の決定
    if step >= 1_000_000:
        return step, "Mb", 1_000_000
    elif step >= 1_000:
        return step, "kb", 1000
    else:
        return step, "bp", 1


def get_scale_bar_params(max_length_bp: int) -> tuple:
    """
    最大遺伝子長に応じて適切なスケールバーの長さと単位を返す

    Args:
        max_length_bp: 最大遺伝子長（bp）

    Returns:
        (scale_bar_bp, unit_label, divisor)
        例: (1000, "kb", 1000) → 1kbのスケールバー
    """
    if max_length_bp >= 100_000:   # 100kb以上
        return 10_000, "kb", 1000
    elif max_length_bp >= 10_000:  # 10kb以上
        return 1_000, "kb", 1000
    elif max_length_bp >= 1_000:   # 1kb以上
        return 100, "bp", 1
    elif max_length_bp >= 100:     # 100bp以上
        return 50, "bp", 1
    else:
        return 10, "bp", 1


def draw_scale_bar(dwg, x_pos: float, y_pos: float, scale_bar_bp: int,
                   shrink_factor: float, scale: float, unit_label: str, divisor: int):
    """
    スケールバーを描画する

    Args:
        dwg: svgwrite.Drawingオブジェクト
        x_pos: スケールバーの左端X座標
        y_pos: スケールバーのY座標
        scale_bar_bp: スケールバーの長さ（bp）
        shrink_factor: 座標の縮小係数
        scale: スケール倍率
        unit_label: 単位ラベル（"bp" or "kb"）
        divisor: 単位変換用の除数
    """
    # スケールバーの幅をピクセルで計算
    bar_width = (scale_bar_bp / shrink_factor) * scale
    bar_height = 6  # 縦線の高さ

    # 水平線
    dwg.add(dwg.line(
        start=(x_pos, y_pos),
        end=(x_pos + bar_width, y_pos),
        stroke='black',
        stroke_width=1.5
    ))

    # 左端の縦線
    dwg.add(dwg.line(
        start=(x_pos, y_pos - bar_height / 2),
        end=(x_pos, y_pos + bar_height / 2),
        stroke='black',
        stroke_width=1.5
    ))

    # 右端の縦線
    dwg.add(dwg.line(
        start=(x_pos + bar_width, y_pos - bar_height / 2),
        end=(x_pos + bar_width, y_pos + bar_height / 2),
        stroke='black',
        stroke_width=1.5
    ))

    # ラベル
    if divisor == 1:
        label_text = f"{scale_bar_bp} {unit_label}"
    else:
        label_text = f"{scale_bar_bp // divisor} {unit_label}"

    dwg.add(dwg.text(
        label_text,
        insert=(x_pos + bar_width / 2, y_pos - 8),
        font_size='11px',
        fill='black',
        text_anchor='middle'
    ))


# =====================
# 描画関数
# =====================

def get_terminal_feature(features, strand="+"):
    """
    遺伝子の終端にある feature を返す。
    優先順位: three_prime_UTR > CDS > exon
    """
    priority = ['three_prime_UTR', 'CDS', 'exon']

    for ftype in priority:
        candidates = [f for f in features if f.feature_type == ftype]
        if candidates:
            if strand == '-':
                return min(candidates, key=lambda f: f.start)
            return max(candidates, key=lambda f: f.end)

    return None


def draw_terminal_feature(dwg, x_start, x_end, y_pos, height_feature, fill_color,
                          stroke_color, outline_enabled, stroke_width, strand="+"):
    tip = min(height_feature // 2, abs(x_end - x_start))
    if strand == '-':
        points = [
            (x_end, y_pos),
            (x_start + tip, y_pos),
            (x_start, y_pos + height_feature / 2),
            (x_start + tip, y_pos + height_feature),
            (x_end, y_pos + height_feature)
        ]
    else:
        points = [
            (x_start, y_pos),
            (x_end - tip, y_pos),
            (x_end, y_pos + height_feature / 2),
            (x_end - tip, y_pos + height_feature),
            (x_start, y_pos + height_feature)
        ]

    dwg.add(
        dwg.polygon(
            points=points,
            fill=fill_color,
            stroke=stroke_color if outline_enabled else 'none',
            stroke_width=stroke_width
        )
    )


def draw_gene_structure(gene: GeneStructure, scale=2, extra_padding=100, shrink_factor=30.0,
                        utr_color=None, exon_color=None, line_color=None, domain_color=None,
                        coordinate_mode="relative", anchor=0, strand="+"):
    # デフォルト色を設定
    utr_color = utr_color or DEFAULT_COLORS['utr_color']
    exon_color = exon_color or DEFAULT_COLORS['exon_color']
    line_color = line_color or DEFAULT_COLORS['line_color']
    domain_color = domain_color or DEFAULT_COLORS['domain_color']

    gene.to_relative()
    all_features = gene.get_sorted_features()

    # Calculate true extents including SNPs and Insertions
    actual_min_start, actual_max_end = gene.get_full_extent()
    gene_strand = gene.strand or strand
    terminal_feature = get_terminal_feature(all_features, gene_strand)

    # 描画用にシフト (内部相対座標 1 を基準にする)
    # 相対座標 1 が LEFT_MARGIN に来るように設定したいが、
    # actual_min_start < 1 の場合に左側にはみ出さないようにマージンを調整する
    drawing_anchor = 1
    
    # 実際に左側にはみ出す量（ピクセル）
    left_overhang = 0
    if actual_min_start < drawing_anchor:
        left_overhang = (drawing_anchor - actual_min_start) / shrink_factor * scale
    
    # 全体の描画幅
    range_bp = actual_max_end - actual_min_start
    
    canvas_width = LEFT_MARGIN + left_overhang + (range_bp / shrink_factor) * scale + extra_padding + 300
    canvas_height = 400

    dwg = svgwrite.Drawing(size=(canvas_width, canvas_height))
    y_pos = 50
    height_feature = 15
    
    # 描画座標計算用のベースオフセット
    # x = LEFT_MARGIN + left_overhang + (pos - drawing_anchor) / shrink_factor * scale
    base_x = LEFT_MARGIN + left_overhang
    max_x_coord = base_x + (actual_max_end - drawing_anchor) / shrink_factor * scale

    # === 座標軸（スケールバー）の描画 ===
    axis_y = y_pos + height_feature + 40
    if range_bp > 0:
        x_axis_start = base_x + (actual_min_start - drawing_anchor) / shrink_factor * scale
        x_axis_end = base_x + (actual_max_end - drawing_anchor) / shrink_factor * scale
        
        dwg.add(dwg.line(
            start=(x_axis_start, axis_y),
            end=(x_axis_end, axis_y),
            stroke='black',
            stroke_width=1
        ))

        tick_interval, unit_label, divisor = get_tick_params(range_bp, shrink_factor, scale)
        display_start = anchor if coordinate_mode == "absolute" else 1
        
        if coordinate_mode == "absolute" and strand == '-':
            max_display_val = display_start - actual_min_start + 1
            first_tick_label = math.floor(max_display_val / tick_interval) * tick_interval
            first_tick = display_start - first_tick_label + 1
        else:
            min_display_val = display_start + actual_min_start - 1
            first_tick_label = math.floor(min_display_val / tick_interval) * tick_interval
            first_tick = first_tick_label - display_start + 1
        
        for tick_val in range(first_tick, actual_max_end + 1, tick_interval):
            if tick_val < actual_min_start - 0.1 or tick_val > actual_max_end + 0.1:
                continue

            x = base_x + (tick_val - drawing_anchor) / shrink_factor * scale
            dwg.add(dwg.line(start=(x, axis_y), end=(x, axis_y + 5), stroke='black', stroke_width=1))

            if coordinate_mode == "absolute" and strand == '-':
                display_tick_val = display_start - tick_val + 1
            else:
                display_tick_val = display_start + tick_val - 1

            tick_label = f"{display_tick_val} {unit_label}" if divisor == 1 else f"{display_tick_val // divisor} {unit_label}"
            dwg.add(dwg.text(tick_label, insert=(x, axis_y - 5), font_size='9px', fill='black', text_anchor='middle'))

    # Draw baseline
    baseline_segments = get_baseline_segments(actual_min_start, actual_max_end, getattr(gene, 'deletion_regions', []))
    y_line = y_pos + height_feature // 2
    for seg_start, seg_end in baseline_segments:
        x_base_start = base_x + (seg_start - drawing_anchor) / shrink_factor * scale
        x_base_end = base_x + (seg_end - drawing_anchor) / shrink_factor * scale
        dwg.add(dwg.line(start=(x_base_start, y_line), end=(x_base_end, y_line), stroke=line_color, stroke_width=1))

    for feat in all_features:
        x_start = base_x + (feat.start - drawing_anchor) / shrink_factor * scale
        x_end = base_x + (feat.end - drawing_anchor) / shrink_factor * scale
        width = x_end - x_start


        if feat.feature_type == 'domain':
            continue

        if feat.feature_type == 'deletion':
            # くの字型の折れ線
            y_line = y_pos + height_feature // 2
            mid_x = x_start + (x_end - x_start) / 2
            offset = 10  # くの字の高さ
            del_color = feat.attributes.get('color', 'black')
            dwg.add(
                dwg.polyline(
                    points=[
                        (x_start, y_line),
                        (mid_x, y_line - offset),
                        (x_end, y_line)
                    ],
                    fill='none',
                    stroke=del_color,
                    stroke_width=1,
                    stroke_dasharray="2,2"
                )
            )
        elif feat.feature_type in ('exon', 'CDS', 'five_prime_UTR', 'three_prime_UTR'):
            # five_prime_UTR と three_prime_UTR は utr_color、exon/CDS は exon_color
            if feat.feature_type in ('five_prime_UTR', 'three_prime_UTR'):
                fill_color = utr_color
            else:
                fill_color = exon_color

            stroke_color = FEATURE_OUTLINES.get(feat.feature_type, 'black')
            stroke_width = FEATURE_OUTLINE_WIDTHS.get(feat.feature_type, 1)
            outline_enabled = FEATURE_OUTLINE_ENABLED.get(feat.feature_type, True)

            # Terminal Feature は矢印形状
            if feat is terminal_feature:
                draw_terminal_feature(
                    dwg, x_start, x_end, y_pos, height_feature, fill_color,
                    stroke_color, outline_enabled, stroke_width, gene_strand
                )
            else:
                dwg.add(
                    dwg.rect(
                        insert=(x_start, y_pos),
                        size=(width, height_feature),
                        fill=fill_color,
                        stroke=stroke_color if outline_enabled else 'none',
                        stroke_width=stroke_width
                    )
                )
        elif feat.feature_type == 'intron':
            if x_start < x_end:
                y_line = y_pos + height_feature // 2
                dwg.add(
                    dwg.line(
                        start=(x_start, y_line),
                        end=(x_end, y_line),
                        stroke=line_color,
                        stroke_width=FEATURE_OUTLINE_WIDTHS.get('intron', 1)
                    )
                )

    # === Insertions ===
    triangle_height = 6
    y_triangle = y_pos - 8  # exon の少し上

    for ins in getattr(gene, "insertions", []):
        # Insertionオブジェクトの場合はpositionとlengthを取得、それ以外は後方互換性のため位置のみ
        if hasattr(ins, 'position'):
            ins_pos = ins.position
            ins_length = getattr(ins, 'length', 1)
            ins_color = getattr(ins, 'color', 'black')
        else:
            ins_pos = ins
            ins_length = 1
            ins_color = "black"

        x = base_x + (ins_pos - drawing_anchor) / shrink_factor * scale
        base_width = get_insertion_base_width(ins_length, shrink_factor, scale)

        dwg.add(
            dwg.polygon(
                points=[
                    (x - base_width / 2, y_triangle),
                    (x + base_width / 2, y_triangle),
                    (x, y_triangle + triangle_height)
                ],
                fill=ins_color,
                stroke=ins_color,
                stroke_width=1.5
            )
        )

    # === SNPs ===
    snp_extend_up = 8
    snp_extend_down = 8
    y_snp_top = y_pos - snp_extend_up
    y_snp_bottom = y_pos + height_feature + snp_extend_down

    for snp in getattr(gene, "snps", []):
        if hasattr(snp, 'position'):
            snp_pos = snp.position
            snp_color = getattr(snp, 'color', 'black')
        else:
            snp_pos = snp
            snp_color = "black"

        x = base_x + (snp_pos - drawing_anchor) / shrink_factor * scale
        dwg.add(
            dwg.line(
                start=(x, y_snp_top),
                end=(x, y_snp_bottom),
                stroke=snp_color,
                stroke_width=1.2
            )
        )

    # ドメインを描画（上層）
    for feat in all_features:
        if feat.feature_type == 'domain':
            x_start = base_x + (feat.start - drawing_anchor) / shrink_factor * scale
            x_end = base_x + (feat.end - drawing_anchor) / shrink_factor * scale
            width = x_end - x_start


            # ドメイン色はattributesから取得
            feat_domain_color = feat.attributes.get('color', domain_color)

            dwg.add(
                dwg.rect(
                    insert=(x_start, y_pos),
                    size=(width, height_feature),
                    fill=feat_domain_color,
                    stroke=FEATURE_OUTLINES.get('domain', 'black'),
                    stroke_width=FEATURE_OUTLINE_WIDTHS.get('domain', 1)
                )
            )

    # === 凡例の動的生成 ===
    present_feature_types = set(f.feature_type for f in all_features)
    legend_items = []

    # CDS がある場合は「CDS」、exon のみの場合は「Exon」と表示
    if 'CDS' in present_feature_types:
        legend_items.append(('CDS', 'CDS', exon_color))
    elif 'exon' in present_feature_types:
        legend_items.append(('exon', 'Exon', exon_color))
    if 'five_prime_UTR' in present_feature_types:
        legend_items.append(('five_prime_UTR', "5' UTR", utr_color))
    if 'three_prime_UTR' in present_feature_types:
        legend_items.append(('three_prime_UTR', "3' UTR", utr_color))
    if 'intron' in present_feature_types:
        legend_items.append(('intron', 'Intron', line_color))
    if 'deletion' in present_feature_types:
        legend_items.append(('deletion', 'Deletion', None))
    if getattr(gene, "insertions", []):
        legend_items.append(('insertion', 'Insertion', None))
    if getattr(gene, "snps", []):
        legend_items.append(('snp', 'SNP', None))
    # ドメインは名前ごとに個別表示
    for domain_name, color in getattr(gene, 'domain_color_map', {}).items():
        legend_items.append(('domain', domain_name, color))

    legend_x = max_x_coord + 100
    legend_y = 30
    box_size = 12
    spacing = 20

    for i, (feat_key, label, color) in enumerate(legend_items):
        y_legend = legend_y + i * spacing
        if feat_key == 'deletion':
            # くの字型
            y_mid = y_legend + box_size // 2
            dwg.add(dwg.polyline(
                points=[(legend_x, y_mid), (legend_x + box_size // 2, y_mid - 6), (legend_x + box_size, y_mid)],
                fill='none',
                stroke='black',
                stroke_width=1.5,
                stroke_dasharray="2,2"
            ))
        elif feat_key == 'insertion':
            # 逆三角形
            y_mid = y_legend + box_size // 2
            dwg.add(dwg.polygon(
                points=[(legend_x, y_mid - 4), (legend_x + box_size, y_mid - 4), (legend_x + box_size // 2, y_mid + 4)],
                fill='black',
                stroke='black',
                stroke_width=1.5
            ))
        elif feat_key == 'snp':
            # 縦線
            dwg.add(dwg.line(
                start=(legend_x + box_size // 2, y_legend),
                end=(legend_x + box_size // 2, y_legend + box_size),
                stroke='black',
                stroke_width=1.2
            ))
        elif feat_key == 'intron':
            y_line = y_legend + box_size // 2
            dwg.add(dwg.line(
                start=(legend_x, y_line),
                end=(legend_x + box_size, y_line),
                stroke=color,
                stroke_width=FEATURE_OUTLINE_WIDTHS.get('intron', 1)
            ))
        else:
            dwg.add(dwg.rect(
                insert=(legend_x, y_legend),
                size=(box_size, box_size),
                fill=color,
                stroke='black'
            ))
        dwg.add(dwg.text(
            label,
            insert=(legend_x + box_size + 5, y_legend + box_size - 2),
            font_size='12px',
            fill='black'
        ))

    return dwg.tostring()


def draw_multiple_gene_structures(
    genes: List[GeneStructure],
    labels: List[str],
    show_labels: bool = True,
    show_scale: bool = False,
    gene_spacing: int = 50,
    label_spacing: int = 10,
    scale: float = 2,
    shrink_factor: float = 30.0,
    utr_color: str = None,
    exon_color: str = None,
    line_color: str = None,
    domain_color: str = None,
    coordinate_mode: str = "relative",
    anchor: int = 0,
    strand: str = "+"
) -> str:
    """
    複数の遺伝子構造を縦並びで1つのSVGに描画する

    Args:
        genes: 描画するGeneStructureのリスト
        labels: 各遺伝子のラベル（transcript_id等）
        show_labels: ラベルを表示するかどうか
        show_scale: スケールバーを表示するかどうか
        gene_spacing: 遺伝子間の余白（ピクセル）
        label_spacing: ラベルと遺伝子構造の余白（ピクセル）
        scale: スケール倍率
        shrink_factor: 座標の縮小係数
        utr_color: UTRの色
        exon_color: Exon/CDSの色
        line_color: イントロンの色
        domain_color: ドメインの色
        coordinate_mode: 座標モード ("relative" or "absolute")
        anchor: 基準となるゲノム座標（absoluteモード用）
        strand: ストランド方向（absoluteモードの座標軸ラベル用）

    Returns:
        SVG文字列
    """
    # デフォルト色を設定
    utr_color = utr_color or DEFAULT_COLORS['utr_color']
    exon_color = exon_color or DEFAULT_COLORS['exon_color']
    line_color = line_color or DEFAULT_COLORS['line_color']
    domain_color = domain_color or DEFAULT_COLORS['domain_color']

    extra_padding = 100
    height_feature = 15
    # ラベルの最大文字数に基づいて基本幅を計算（monospace 11px ≈ 6.6px/文字）
    max_label_len = max(len(label) for label in labels) if labels else 0
    label_base_width = int(max_label_len * 6.6) + 5  # 少し余裕を持たせる
    label_width = (label_base_width + label_spacing) if show_labels else 0  # ラベル用のスペース + 余白

    # 各遺伝子の座標範囲を計算
    gene_data = []

    for gene in genes:
        gene.to_relative()
        all_features = gene.get_sorted_features()
        if not all_features:
            gene_data.append((all_features, 1, 1))
            continue

        # Calculate true extents including SNPs and Insertions
        actual_min_start, actual_max_end = gene.get_full_extent()
        
        gene_data.append((all_features, actual_min_start, actual_max_end))

    # 全体の最小・最大座標を決定して位置を揃える
    global_min_start = min(g[1] for g in gene_data) if gene_data else 1
    global_max_end = max(g[2] for g in gene_data) if gene_data else 1
    global_shift = -global_min_start

    # Canvas幅を計算
    global_max_x = LEFT_MARGIN + label_width + (global_max_end / shrink_factor + global_shift / shrink_factor) * scale
    canvas_width = global_max_x + extra_padding + 300

    # スケールバー（座標軸）の設定
    scale_bar_height = 40 if show_scale else 0
    top_margin = 30 + scale_bar_height

    # Canvas高さ = (遺伝子高さ + 余白) × 遺伝子数 + 上下マージン
    gene_height = height_feature + 10  # 遺伝子1つ分の高さ
    canvas_height = top_margin + len(genes) * (gene_height + gene_spacing) + 150  # 凡例用スペース

    # メモリ上にSVGを作成
    dwg = svgwrite.Drawing(size=(canvas_width, canvas_height))

    # === スケールバー（座標軸）の描画 ===
    if show_scale:
        range_bp = global_max_end - global_min_start
        if range_bp > 0:
            axis_y = top_margin - 25
            
            x_axis_start = LEFT_MARGIN + label_width + (global_min_start / shrink_factor + global_shift / shrink_factor) * scale
            x_axis_end = LEFT_MARGIN + label_width + (global_max_end / shrink_factor + global_shift / shrink_factor) * scale

            # 座標軸の線
            dwg.add(dwg.line(
                start=(x_axis_start, axis_y),
                end=(x_axis_end, axis_y),
                stroke='black',
                stroke_width=1
            ))

            # 目盛りの計算
            tick_interval, unit_label, divisor = get_tick_params(range_bp, shrink_factor, scale)
            
            # coordinate_mode に応じて開始座標を決定
            display_start = anchor if coordinate_mode == "absolute" else 1
            
            # 良い感じの目盛り値を計算するために、表示値ベースで最初の目盛りを決定
            if coordinate_mode == "absolute" and strand == '-':
                max_display_val = display_start - global_min_start + 1
                first_tick_label = math.floor(max_display_val / tick_interval) * tick_interval
                first_tick = display_start - first_tick_label + 1
            else:
                min_display_val = display_start + global_min_start - 1
                first_tick_label = math.floor(min_display_val / tick_interval) * tick_interval
                first_tick = first_tick_label - display_start + 1
            
            for tick_val in range(first_tick, global_max_end + 1, tick_interval):
                # 実際のデータ範囲外の目盛りは描画しない
                if tick_val < global_min_start - 0.1 or tick_val > global_max_end + 0.1:
                    continue

                x = LEFT_MARGIN + label_width + (tick_val / shrink_factor + global_shift / shrink_factor) * scale
                
                # 目盛り線
                dwg.add(dwg.line(
                    start=(x, axis_y),
                    end=(x, axis_y + 5),
                    stroke='black',
                    stroke_width=1
                ))

                # ラベル
                if coordinate_mode == "absolute" and strand == '-':
                    display_tick_val = display_start - tick_val + 1
                else:
                    display_tick_val = display_start + tick_val - 1

                if divisor == 1:
                    tick_label = f"{display_tick_val} {unit_label}"
                else:
                    tick_label = f"{display_tick_val // divisor} {unit_label}"
                
                dwg.add(dwg.text(
                    tick_label,
                    insert=(x, axis_y - 5),
                    font_size='9px',
                    fill='black',
                    text_anchor='middle'
                ))

    # 各遺伝子を描画
    for idx, (gene, label) in enumerate(zip(genes, labels)):
        all_features, actual_min_start, actual_max_end = gene_data[idx]
        y_pos = top_margin + idx * (gene_height + gene_spacing)
        terminal_feature = get_terminal_feature(all_features, gene.strand)

        # ラベルを描画
        if show_labels:
            dwg.add(dwg.text(
                label,
                insert=(LEFT_MARGIN, y_pos + height_feature - 2),
                font_size='11px',
                fill='black',
                font_family='monospace'
            ))

        # Draw baseline (intron style) in segments, skipping deletions
        baseline_segments = get_baseline_segments(global_min_start, global_max_end, getattr(gene, 'deletion_regions', []))
        y_line = y_pos + height_feature // 2
        for seg_start, seg_end in baseline_segments:
            x_base_start = LEFT_MARGIN + label_width + (seg_start / shrink_factor + global_shift / shrink_factor) * scale
            x_base_end = LEFT_MARGIN + label_width + (seg_end / shrink_factor + global_shift / shrink_factor) * scale
            dwg.add(
                dwg.line(
                    start=(x_base_start, y_line),
                    end=(x_base_end, y_line),
                    stroke=line_color,
                    stroke_width=FEATURE_OUTLINE_WIDTHS.get('intron', 1)
                )
            )

        # フィーチャーを描画（ドメイン以外）
        for feat in all_features:
            x_start = LEFT_MARGIN + label_width + (feat.start / shrink_factor + global_shift / shrink_factor) * scale
            x_end = LEFT_MARGIN + label_width + (feat.end / shrink_factor + global_shift / shrink_factor) * scale
            width = x_end - x_start

            if feat.feature_type == 'domain':
                continue

            if feat.feature_type == 'deletion':
                # くの字型の折れ線
                y_line = y_pos + height_feature // 2
                mid_x = x_start + (x_end - x_start) / 2
                offset = 10
                del_color = feat.attributes.get('color', 'black')
                dwg.add(
                    dwg.polyline(
                        points=[
                            (x_start, y_line),
                            (mid_x, y_line - offset),
                            (x_end, y_line)
                        ],
                        fill='none',
                        stroke=del_color,
                        stroke_width=1,
                        stroke_dasharray="2,2"
                    )
                )
            elif feat.feature_type in ('exon', 'CDS', 'five_prime_UTR', 'three_prime_UTR'):
                if feat.feature_type in ('five_prime_UTR', 'three_prime_UTR'):
                    fill_color = utr_color
                else:
                    fill_color = exon_color

                stroke_color = FEATURE_OUTLINES.get(feat.feature_type, 'black')
                stroke_width = FEATURE_OUTLINE_WIDTHS.get(feat.feature_type, 1)
                outline_enabled = FEATURE_OUTLINE_ENABLED.get(feat.feature_type, True)

                # Terminal Feature は矢印形状
                if feat is terminal_feature:
                    draw_terminal_feature(
                        dwg, x_start, x_end, y_pos, height_feature, fill_color,
                        stroke_color, outline_enabled, stroke_width, gene.strand
                    )
                else:
                    dwg.add(
                        dwg.rect(
                            insert=(x_start, y_pos),
                            size=(width, height_feature),
                            fill=fill_color,
                            stroke=stroke_color if outline_enabled else 'none',
                            stroke_width=stroke_width
                        )
                    )
            elif feat.feature_type == 'intron':
                if x_start < x_end:
                    y_line = y_pos + height_feature // 2
                    dwg.add(
                        dwg.line(
                            start=(x_start, y_line),
                            end=(x_end, y_line),
                            stroke=line_color,
                            stroke_width=FEATURE_OUTLINE_WIDTHS.get('intron', 1)
                        )
                    )

        # === Insertions ===
        triangle_height = 6
        y_triangle = y_pos - 8

        for ins in getattr(gene, "insertions", []):
            # Insertionオブジェクトの場合はpositionとlengthを取得、それ以外は後方互換性のため位置のみ
            if hasattr(ins, 'position'):
                ins_pos = ins.position
                ins_length = getattr(ins, 'length', 1)
                ins_color = getattr(ins, 'color', 'black')
            else:
                ins_pos = ins
                ins_length = 1
                ins_color = "black"

            x = LEFT_MARGIN + label_width + (ins_pos / shrink_factor + global_shift / shrink_factor) * scale
            base_width = get_insertion_base_width(ins_length, shrink_factor, scale)

            dwg.add(
                dwg.polygon(
                    points=[
                        (x - base_width / 2, y_triangle),
                        (x + base_width / 2, y_triangle),
                        (x, y_triangle + triangle_height)
                    ],
                    fill=ins_color,
                    stroke=ins_color,
                    stroke_width=1.5
                )
            )

        # === SNPs ===
        snp_extend_up = 8
        snp_extend_down = 8
        y_snp_top = y_pos - snp_extend_up
        y_snp_bottom = y_pos + height_feature + snp_extend_down

        for snp in getattr(gene, "snps", []):
            if hasattr(snp, "position"):
                snp_pos = snp.position
                snp_color = getattr(snp, "color", "black")
            else:
                snp_pos = snp
                snp_color = "black"

            x = LEFT_MARGIN + label_width + (snp_pos / shrink_factor + global_shift / shrink_factor) * scale
            dwg.add(
                dwg.line(
                    start=(x, y_snp_top),
                    end=(x, y_snp_bottom),
                    stroke=snp_color,
                    stroke_width=1.2
                )
            )

        # ドメインを描画（上層）
        for feat in all_features:
            if feat.feature_type == 'domain':
                x_start = LEFT_MARGIN + label_width + (feat.start / shrink_factor + global_shift / shrink_factor) * scale
                x_end = LEFT_MARGIN + label_width + (feat.end / shrink_factor + global_shift / shrink_factor) * scale
                width = x_end - x_start

                # ドメイン色はattributesから取得
                feat_domain_color = feat.attributes.get('color', domain_color)

                dwg.add(
                    dwg.rect(
                        insert=(x_start, y_pos),
                        size=(width, height_feature),
                        fill=feat_domain_color,
                        stroke=FEATURE_OUTLINES.get('domain', 'black'),
                        stroke_width=FEATURE_OUTLINE_WIDTHS.get('domain', 1)
                    )
                )

    # === 凡例の動的生成 ===
    # 全遺伝子のfeature typeを収集
    all_feature_types = set()
    all_domain_colors = {}
    has_insertions = False
    has_snps = False
    for gene in genes:
        for f in gene.get_sorted_features():
            all_feature_types.add(f.feature_type)
        all_domain_colors.update(getattr(gene, 'domain_color_map', {}))
        if getattr(gene, "insertions", []):
            has_insertions = True
        if getattr(gene, "snps", []):
            has_snps = True

    # 凡例アイテムを動的に構築
    legend_items = []
    # CDS がある場合は「CDS」、exon のみの場合は「Exon」と表示
    if 'CDS' in all_feature_types:
        legend_items.append(('CDS', 'CDS', exon_color))
    elif 'exon' in all_feature_types:
        legend_items.append(('exon', 'Exon', exon_color))
    if 'five_prime_UTR' in all_feature_types:
        legend_items.append(('five_prime_UTR', "5' UTR", utr_color))
    if 'three_prime_UTR' in all_feature_types:
        legend_items.append(('three_prime_UTR', "3' UTR", utr_color))
    if 'intron' in all_feature_types:
        legend_items.append(('intron', 'Intron', line_color))
    if 'deletion' in all_feature_types:
        legend_items.append(('deletion', 'Deletion', None))
    if has_insertions:
        legend_items.append(('insertion', 'Insertion', None))
    if has_snps:
        legend_items.append(('snp', 'SNP', None))
    # ドメインは名前ごとに個別表示
    for domain_name, color in all_domain_colors.items():
        legend_items.append(('domain', domain_name, color))

    legend_x = global_max_x + 50
    legend_y = 30
    box_size = 12
    spacing = 20

    for i, (feat_key, label_text, color) in enumerate(legend_items):
        y_legend = legend_y + i * spacing
        if feat_key == 'deletion':
            # くの字型
            y_mid = y_legend + box_size // 2
            dwg.add(dwg.polyline(
                points=[(legend_x, y_mid), (legend_x + box_size // 2, y_mid - 6), (legend_x + box_size, y_mid)],
                fill='none',
                stroke='black',
                stroke_width=1.5,
                stroke_dasharray="2,2"
            ))
        elif feat_key == 'insertion':
            # 逆三角形
            y_mid = y_legend + box_size // 2
            dwg.add(dwg.polygon(
                points=[(legend_x, y_mid - 4), (legend_x + box_size, y_mid - 4), (legend_x + box_size // 2, y_mid + 4)],
                fill='black',
                stroke='black',
                stroke_width=1.5
            ))
        elif feat_key == 'snp':
            # 縦線
            dwg.add(dwg.line(
                start=(legend_x + box_size // 2, y_legend),
                end=(legend_x + box_size // 2, y_legend + box_size),
                stroke='black',
                stroke_width=1.2
            ))
        elif feat_key == 'intron':
            y_line = y_legend + box_size // 2
            dwg.add(dwg.line(
                start=(legend_x, y_line),
                end=(legend_x + box_size, y_line),
                stroke=color,
                stroke_width=FEATURE_OUTLINE_WIDTHS.get('intron', 1)
            ))
        else:
            dwg.add(dwg.rect(
                insert=(legend_x, y_legend),
                size=(box_size, box_size),
                fill=color,
                stroke='black'
            ))
        dwg.add(dwg.text(
            label_text,
            insert=(legend_x + box_size + 5, y_legend + box_size - 2),
            font_size='12px',
            fill='black'
        ))

    return dwg.tostring()


def draw_region_gene_structures(
    genes: List[GeneStructure],
    labels: List[str],
    region_start: int,
    region_end: int,
    show_labels: bool = True,
    gene_spacing: int = 50,
    label_spacing: int = 10,
    scale: float = 2,
    shrink_factor: float = 30.0,
    utr_color: str = None,
    exon_color: str = None,
    line_color: str = None,
    domain_color: str = None
) -> str:
    """
    共通座標軸上に複数の遺伝子構造を描画する
    座標が重複しない遺伝子は同じトラック（行）に横並びで配置

    Args:
        genes: 描画するGeneStructureのリスト
        labels: 各遺伝子のラベル
        region_start: 表示領域の開始座標（ゲノム座標）
        region_end: 表示領域の終了座標（ゲノム座標）
        show_labels: ラベルを表示するかどうか
        gene_spacing: トラック間の余白（ピクセル）
        label_spacing: ラベルと遺伝子構造の余白（ピクセル）
        scale: スケール倍率
        shrink_factor: 座標の縮小係数
        utr_color: UTRの色
        exon_color: Exon/CDSの色
        line_color: イントロンの色
        domain_color: ドメインの色

    Returns:
        SVG文字列
    """
    # デフォルト色を設定
    utr_color = utr_color or DEFAULT_COLORS['utr_color']
    exon_color = exon_color or DEFAULT_COLORS['exon_color']
    line_color = line_color or DEFAULT_COLORS['line_color']
    domain_color = domain_color or DEFAULT_COLORS['domain_color']

    height_feature = 15

    # 各遺伝子の座標範囲を計算
    gene_ranges = []
    for idx, gene in enumerate(genes):
        # Calculate true extents including SNPs and Insertions
        gene_start, gene_end = gene.get_full_extent()
            
        gene_ranges.append({
            'idx': idx,
            'gene': gene,
            'label': labels[idx],
            'start': gene_start,
            'end': gene_end
        })

    # 開始座標でソート
    gene_ranges.sort(key=lambda x: x['start'])

    # トラック配置アルゴリズム（重複しない遺伝子は同じトラックに配置）
    tracks = []  # 各トラックの終了座標を保持
    gene_track_assignments = []  # 各遺伝子のトラック番号

    for gene_info in gene_ranges:
        gene_start = gene_info['start']
        gene_end = gene_info['end']

        # 配置可能なトラックを探す（余白を考慮）
        track_found = False
        min_gap = 500  # 遺伝子間の最小間隔（bp）

        for track_idx, track_end in enumerate(tracks):
            if gene_start > track_end + min_gap:
                # このトラックに配置可能
                tracks[track_idx] = gene_end
                gene_track_assignments.append((gene_info, track_idx))
                track_found = True
                break

        if not track_found:
            # 新しいトラックを作成
            tracks.append(gene_end)
            gene_track_assignments.append((gene_info, len(tracks) - 1))

    num_tracks = len(tracks)

    # 全遺伝子の座標範囲を計算（はみ出しを含む）
    all_starts = [g['start'] for g in gene_ranges]
    all_ends = [g['end'] for g in gene_ranges]

    # 描画範囲を決定（領域指定とはみ出しを考慮）
    if all_starts and all_ends:
        draw_start = min(region_start, min(all_starts))
        draw_end = max(region_end, max(all_ends))
    else:
        draw_start = region_start
        draw_end = region_end

    # 座標軸の幅を計算
    axis_width = (draw_end - draw_start) / shrink_factor * scale

    # Canvas幅
    extra_padding = 100
    canvas_width = LEFT_MARGIN + axis_width + extra_padding + 300

    # Canvas高さ（ラベルは遺伝子構造の下に表示するため、トラックごとに追加スペース）
    label_height = 15 if show_labels else 0
    track_height = height_feature + label_height + label_spacing
    top_margin = 50  # 座標軸用のスペース
    canvas_height = top_margin + num_tracks * (track_height + gene_spacing) + 150

    # メモリ上にSVGを作成
    dwg = svgwrite.Drawing(size=(canvas_width, canvas_height))

    # 座標軸を描画（上部）
    axis_y = top_margin - 20
    dwg.add(dwg.line(
        start=(LEFT_MARGIN, axis_y),
        end=(LEFT_MARGIN + axis_width, axis_y),
        stroke='black',
        stroke_width=1
    ))

    # 目盛りを描画
    tick_interval, unit_label, divisor = get_tick_params(draw_end - draw_start, shrink_factor, scale)
    first_tick = math.floor(draw_start / tick_interval) * tick_interval

    for tick_pos in range(first_tick, draw_end + 1, tick_interval):
        # 描画範囲外の tick は描画しない
        if tick_pos < draw_start - 0.1 or tick_pos > draw_end + 0.1:
            continue
        
        x = LEFT_MARGIN + (tick_pos - draw_start) / shrink_factor * scale

        # 目盛り線
        dwg.add(dwg.line(
            start=(x, axis_y),
            end=(x, axis_y + 5),
            stroke='black',
            stroke_width=1
        ))

        # ラベル
        if divisor == 1:
            tick_label = f"{tick_pos} {unit_label}"
        else:
            tick_label = f"{tick_pos // divisor} {unit_label}"
        dwg.add(dwg.text(
            tick_label,
            insert=(x, axis_y - 3),
            font_size='9px',
            fill='black',
            text_anchor='middle'
        ))

    # 各遺伝子を描画
    for gene_info, track_idx in gene_track_assignments:
        gene = gene_info['gene']
        label = gene_info['label']
        actual_min_start = gene_info['start']
        actual_max_end = gene_info['end']
        structural_start, structural_end = get_structural_extent(gene)
        all_features = gene.get_sorted_features()
        y_pos = top_margin + track_idx * (track_height + gene_spacing)
        terminal_feature = get_terminal_feature(all_features, gene.strand)

        # Draw baseline (intron style) in segments, skipping deletions
        baseline_segments = get_baseline_segments(structural_start, structural_end, getattr(gene, 'deletion_regions', []))
        y_line = y_pos + height_feature // 2
        for seg_start, seg_end in baseline_segments:
            x_base_start = LEFT_MARGIN + (seg_start - draw_start) / shrink_factor * scale
            x_base_end = LEFT_MARGIN + (seg_end - draw_start) / shrink_factor * scale
            dwg.add(
                dwg.line(
                    start=(x_base_start, y_line),
                    end=(x_base_end, y_line),
                    stroke=line_color,
                    stroke_width=FEATURE_OUTLINE_WIDTHS.get('intron', 1)
                )
            )

        # 遺伝子の中心X座標を計算（ラベル配置用）
        gene_center_x = None
        if actual_min_start < actual_max_end:
            gene_center_x = LEFT_MARGIN + ((actual_min_start + actual_max_end) / 2 - draw_start) / shrink_factor * scale

        # フィーチャーを描画（ドメイン以外）
        for feat in all_features:
            # X座標 = 描画範囲の開始位置からのオフセット
            x_start = LEFT_MARGIN + (feat.start - draw_start) / shrink_factor * scale
            x_end = LEFT_MARGIN + (feat.end - draw_start) / shrink_factor * scale
            width = x_end - x_start

            if feat.feature_type == 'domain':
                continue

            if feat.feature_type == 'deletion':
                # くの字型の折れ線
                y_line = y_pos + height_feature // 2
                mid_x = x_start + (x_end - x_start) / 2
                offset = 10
                del_color = feat.attributes.get('color', 'black')
                dwg.add(
                    dwg.polyline(
                        points=[
                            (x_start, y_line),
                            (mid_x, y_line - offset),
                            (x_end, y_line)
                        ],
                        fill='none',
                        stroke=del_color,
                        stroke_width=1,
                        stroke_dasharray="2,2"
                    )
                )
            elif feat.feature_type in ('exon', 'CDS', 'five_prime_UTR', 'three_prime_UTR'):
                if feat.feature_type in ('five_prime_UTR', 'three_prime_UTR'):
                    fill_color = utr_color
                else:
                    fill_color = exon_color

                stroke_color = FEATURE_OUTLINES.get(feat.feature_type, 'black')
                stroke_width = FEATURE_OUTLINE_WIDTHS.get(feat.feature_type, 1)
                outline_enabled = FEATURE_OUTLINE_ENABLED.get(feat.feature_type, True)

                # Terminal Feature は矢印形状
                if feat is terminal_feature:
                    draw_terminal_feature(
                        dwg, x_start, x_end, y_pos, height_feature, fill_color,
                        stroke_color, outline_enabled, stroke_width, gene.strand
                    )
                else:
                    dwg.add(
                        dwg.rect(
                            insert=(x_start, y_pos),
                            size=(width, height_feature),
                            fill=fill_color,
                            stroke=stroke_color if outline_enabled else 'none',
                            stroke_width=stroke_width
                        )
                    )
            elif feat.feature_type == 'intron':
                if x_start < x_end:
                    y_line = y_pos + height_feature // 2
                    dwg.add(
                        dwg.line(
                            start=(x_start, y_line),
                            end=(x_end, y_line),
                            stroke=line_color,
                            stroke_width=FEATURE_OUTLINE_WIDTHS.get('intron', 1)
                        )
                    )

        # === Insertions ===
        triangle_height = 6
        y_triangle = y_pos - 8

        for ins in getattr(gene, "insertions", []):
            # Insertionオブジェクトの場合はpositionとlengthを取得、それ以外は後方互換性のため位置のみ
            if hasattr(ins, 'position'):
                ins_pos = ins.position
                ins_length = getattr(ins, 'length', 1)
                ins_color = getattr(ins, 'color', 'black')
            else:
                ins_pos = ins
                ins_length = 1
                ins_color = "black"

            x = LEFT_MARGIN + (ins_pos - draw_start) / shrink_factor * scale
            base_width = get_insertion_base_width(ins_length, shrink_factor, scale)

            dwg.add(
                dwg.polygon(
                    points=[
                        (x - base_width / 2, y_triangle),
                        (x + base_width / 2, y_triangle),
                        (x, y_triangle + triangle_height)
                    ],
                    fill=ins_color,
                    stroke=ins_color,
                    stroke_width=1.5
                )
            )

        # === SNPs ===
        snp_extend_up = 8
        snp_extend_down = 8
        y_snp_top = y_pos - snp_extend_up
        y_snp_bottom = y_pos + height_feature + snp_extend_down

        for snp in getattr(gene, "snps", []):
            if hasattr(snp, "position"):
                snp_pos = snp.position
                snp_color = getattr(snp, "color", "black")
            else:
                snp_pos = snp
                snp_color = "black"

            x = LEFT_MARGIN + (snp_pos - draw_start) / shrink_factor * scale
            dwg.add(
                dwg.line(
                    start=(x, y_snp_top),
                    end=(x, y_snp_bottom),
                    stroke=snp_color,
                    stroke_width=1.2
                )
            )

        # ドメインを描画（上層）
        for feat in all_features:
            if feat.feature_type == 'domain':
                x_start = LEFT_MARGIN + (feat.start - draw_start) / shrink_factor * scale
                x_end = LEFT_MARGIN + (feat.end - draw_start) / shrink_factor * scale
                width = x_end - x_start

                # ドメイン色はattributesから取得
                feat_domain_color = feat.attributes.get('color', domain_color)

                dwg.add(
                    dwg.rect(
                        insert=(x_start, y_pos),
                        size=(width, height_feature),
                        fill=feat_domain_color,
                        stroke=FEATURE_OUTLINES.get('domain', 'black'),
                        stroke_width=FEATURE_OUTLINE_WIDTHS.get('domain', 1)
                    )
                )

        # ラベルを遺伝子構造の下に描画（中央揃え）
        if show_labels and gene_center_x is not None:
            dwg.add(dwg.text(
                label,
                insert=(gene_center_x, y_pos + height_feature + label_spacing + 10),
                font_size='10px',
                fill='black',
                font_family='monospace',
                text_anchor='middle'
            ))

    # === 凡例の動的生成 ===
    # 全遺伝子のfeature typeを収集
    all_feature_types = set()
    all_domain_colors = {}
    unique_insertion_colors = set()
    unique_snp_colors = set()
    unique_deletion_colors = set()

    for gene in genes:
        for f in gene.get_sorted_features():
            all_feature_types.add(f.feature_type)
            if f.feature_type == 'deletion':
                unique_deletion_colors.add(f.attributes.get('color', 'black'))
        all_domain_colors.update(getattr(gene, 'domain_color_map', {}))
        for ins in getattr(gene, "insertions", []):
            unique_insertion_colors.add(getattr(ins, 'color', 'black'))
        for snp in getattr(gene, "snps", []):
            unique_snp_colors.add(getattr(snp, 'color', 'black'))

    # 凡例アイテムを動的に構築
    legend_items = []
    # CDS がある場合は「CDS」、exon のみの場合は「Exon」と表示
    if 'CDS' in all_feature_types:
        legend_items.append(('CDS', 'CDS', exon_color))
    elif 'exon' in all_feature_types:
        legend_items.append(('exon', 'Exon', exon_color))
    if 'five_prime_UTR' in all_feature_types:
        legend_items.append(('five_prime_UTR', "5' UTR", utr_color))
    if 'three_prime_UTR' in all_feature_types:
        legend_items.append(('three_prime_UTR', "3' UTR", utr_color))
    if 'intron' in all_feature_types:
        legend_items.append(('intron', 'Intron', line_color))
    
    # バリアントは色ごとに表示（黒以外がある場合）
    for color in sorted(list(unique_deletion_colors)):
        label = "Deletion" if color == "black" else f"Deletion ({color})"
        legend_items.append(('deletion', label, color))
    
    for color in sorted(list(unique_insertion_colors)):
        label = "Insertion" if color == "black" else f"Insertion ({color})"
        legend_items.append(('insertion', label, color))
    
    for color in sorted(list(unique_snp_colors)):
        label = "SNP" if color == "black" else f"SNP ({color})"
        legend_items.append(('snp', label, color))

    # ドメインは名前ごとに個別表示
    for domain_name, color in all_domain_colors.items():
        legend_items.append(('domain', domain_name, color))

    legend_x = LEFT_MARGIN + axis_width + 50
    legend_y = 30
    box_size = 12
    spacing = 20

    for i, (feat_key, label_text, color) in enumerate(legend_items):
        y_legend = legend_y + i * spacing
        if feat_key == 'deletion':
            # くの字型
            y_mid = y_legend + box_size // 2
            stroke_color = color if color else 'black'
            dwg.add(dwg.polyline(
                points=[(legend_x, y_mid), (legend_x + box_size // 2, y_mid - 6), (legend_x + box_size, y_mid)],
                fill='none',
                stroke=stroke_color,
                stroke_width=1.5,
                stroke_dasharray="2,2"
            ))
        elif feat_key == 'insertion':
            # 逆三角形
            y_mid = y_legend + box_size // 2
            fill_color = color if color else 'black'
            dwg.add(dwg.polygon(
                points=[(legend_x, y_mid - 4), (legend_x + box_size, y_mid - 4), (legend_x + box_size // 2, y_mid + 4)],
                fill=fill_color,
                stroke=fill_color,
                stroke_width=1.5
            ))
        elif feat_key == 'snp':
            # 縦線
            stroke_color = color if color else 'black'
            dwg.add(dwg.line(
                start=(legend_x + box_size // 2, y_legend),
                end=(legend_x + box_size // 2, y_legend + box_size),
                stroke=stroke_color,
                stroke_width=1.2
            ))
        elif feat_key == 'intron':
            y_line = y_legend + box_size // 2
            dwg.add(dwg.line(
                start=(legend_x, y_line),
                end=(legend_x + box_size, y_line),
                stroke=color,
                stroke_width=FEATURE_OUTLINE_WIDTHS.get('intron', 1)
            ))
        else:
            dwg.add(dwg.rect(
                insert=(legend_x, y_legend),
                size=(box_size, box_size),
                fill=color,
                stroke='black'
            ))
        dwg.add(dwg.text(
            label_text,
            insert=(legend_x + box_size + 5, y_legend + box_size - 2),
            font_size='12px',
            fill='black'
        ))

    return dwg.tostring()
