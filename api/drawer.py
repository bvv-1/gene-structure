import io
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

def get_tick_params(range_size: int) -> tuple:
    """
    範囲サイズに応じて適切な目盛り間隔と単位を返す

    Args:
        range_size: 表示範囲のサイズ（bp）

    Returns:
        (tick_interval, unit_label, divisor)
        例: (1000, "kb", 1000) → 1kbごとに目盛り、ラベルは "1 kb", "2 kb"...
    """
    if range_size >= 10_000_000:  # 10Mb以上
        return 1_000_000, "Mb", 1_000_000
    elif range_size >= 1_000_000:  # 1Mb以上
        return 100_000, "kb", 1000
    elif range_size >= 100_000:   # 100kb以上
        return 10_000, "kb", 1000
    elif range_size >= 10_000:    # 10kb以上
        return 1_000, "kb", 1000
    elif range_size >= 1_000:     # 1kb以上
        return 100, "bp", 1
    else:
        return 10, "bp", 1


# =====================
# 描画関数
# =====================

def get_terminal_feature(features):
    """
    右端（最大 end）にある feature を返す。
    優先順位: three_prime_UTR > CDS > exon
    """
    priority = ['three_prime_UTR', 'CDS', 'exon']

    for ftype in priority:
        candidates = [f for f in features if f.feature_type == ftype]
        if candidates:
            return max(candidates, key=lambda f: f.end)

    return None


def draw_gene_structure(gene: GeneStructure, scale=2, extra_padding=100, shrink_factor=30.0,
                        utr_color=None, exon_color=None, line_color=None, domain_color=None):
    # デフォルト色を設定
    utr_color = utr_color or DEFAULT_COLORS['utr_color']
    exon_color = exon_color or DEFAULT_COLORS['exon_color']
    line_color = line_color or DEFAULT_COLORS['line_color']
    domain_color = domain_color or DEFAULT_COLORS['domain_color']

    min_start = gene.to_relative()
    all_features = gene.get_sorted_features()
    terminal_feature = get_terminal_feature(all_features)
    max_end = max(f.end / shrink_factor for f in all_features)

    shift = -min_start if min_start < 0 else 0

    canvas_width = LEFT_MARGIN + (max_end + shift / shrink_factor) * scale + extra_padding + 300
    canvas_height = 300  # 凡例分のスペースを確保

    # メモリ上にSVGを作成
    dwg = svgwrite.Drawing(size=(canvas_width, canvas_height))
    y_pos = 50
    height_feature = 15
    max_x_coord = LEFT_MARGIN + (max_end + shift / shrink_factor) * scale

    for feat in all_features:
        x_start = LEFT_MARGIN + (feat.start / shrink_factor + shift / shrink_factor) * scale
        x_end = LEFT_MARGIN + (feat.end / shrink_factor + shift / shrink_factor) * scale
        width = x_end - x_start

        if feat.feature_type == 'domain':
            continue

        if feat.feature_type == 'deletion':
            # くの字型の折れ線
            y_line = y_pos + height_feature // 2
            mid_x = x_start + (x_end - x_start) / 2
            offset = 10  # くの字の高さ
            dwg.add(
                dwg.polyline(
                    points=[
                        (x_start, y_line),
                        (mid_x, y_line - offset),
                        (x_end, y_line)
                    ],
                    fill='none',
                    stroke='black',
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
                tip = height_feature // 2
                dwg.add(
                    dwg.polygon(
                        points=[
                            (x_start, y_pos),
                            (x_end - tip, y_pos),
                            (x_end, y_pos + height_feature / 2),
                            (x_end - tip, y_pos + height_feature),
                            (x_start, y_pos + height_feature)
                        ],
                        fill=fill_color,
                        stroke=stroke_color if outline_enabled else 'none',
                        stroke_width=stroke_width
                    )
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
        else:
            ins_pos = ins
            ins_length = 1

        x = LEFT_MARGIN + (ins_pos / shrink_factor + shift / shrink_factor) * scale
        base_width = get_insertion_base_width(ins_length, shrink_factor, scale)

        dwg.add(
            dwg.polygon(
                points=[
                    (x - base_width / 2, y_triangle),
                    (x + base_width / 2, y_triangle),
                    (x, y_triangle + triangle_height)
                ],
                fill="black",
                stroke="black",
                stroke_width=1.5
            )
        )

    # === SNPs ===
    snp_extend_up = 8
    snp_extend_down = 8
    y_snp_top = y_pos - snp_extend_up
    y_snp_bottom = y_pos + height_feature + snp_extend_down

    for snp_pos in getattr(gene, "snps", []):
        x = LEFT_MARGIN + (snp_pos / shrink_factor + shift / shrink_factor) * scale
        dwg.add(
            dwg.line(
                start=(x, y_snp_top),
                end=(x, y_snp_bottom),
                stroke="black",
                stroke_width=1.2
            )
        )

    # ドメインを描画（上層）
    for feat in all_features:
        if feat.feature_type == 'domain':
            x_start = LEFT_MARGIN + (feat.start / shrink_factor + shift / shrink_factor) * scale
            x_end = LEFT_MARGIN + (feat.end / shrink_factor + shift / shrink_factor) * scale
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
    複数の遺伝子構造を縦並びで1つのSVGに描画する

    Args:
        genes: 描画するGeneStructureのリスト
        labels: 各遺伝子のラベル（transcript_id等）
        show_labels: ラベルを表示するかどうか
        gene_spacing: 遺伝子間の余白（ピクセル）
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

    extra_padding = 100
    height_feature = 15
    # ラベルの最大文字数に基づいて基本幅を計算（monospace 11px ≈ 6.6px/文字）
    max_label_len = max(len(label) for label in labels) if labels else 0
    label_base_width = int(max_label_len * 6.6) + 5  # 少し余裕を持たせる
    label_width = (label_base_width + label_spacing) if show_labels else 0  # ラベル用のスペース + 余白

    # 各遺伝子の最大X座標を計算
    max_x_coords = []
    gene_data = []

    for gene in genes:
        min_start = gene.to_relative()
        all_features = gene.get_sorted_features()
        if not all_features:
            max_x_coords.append(0)
            gene_data.append((all_features, 0, 0))
            continue

        max_end = max(f.end / shrink_factor for f in all_features)
        shift = -min_start if min_start < 0 else 0
        max_x_coord = LEFT_MARGIN + label_width + (max_end + shift / shrink_factor) * scale
        max_x_coords.append(max_x_coord)
        gene_data.append((all_features, shift, max_end))

    # Canvas幅は最大のX座標 + 凡例スペース
    global_max_x = max(max_x_coords) if max_x_coords else LEFT_MARGIN + label_width
    canvas_width = global_max_x + extra_padding + 300

    # Canvas高さ = (遺伝子高さ + 余白) × 遺伝子数 + 上下マージン
    gene_height = height_feature + 10  # 遺伝子1つ分の高さ
    top_margin = 30
    canvas_height = top_margin + len(genes) * (gene_height + gene_spacing) + 150  # 凡例用スペース

    # メモリ上にSVGを作成
    dwg = svgwrite.Drawing(size=(canvas_width, canvas_height))

    # 各遺伝子を描画
    for idx, (gene, label) in enumerate(zip(genes, labels)):
        all_features, shift, max_end = gene_data[idx]
        y_pos = top_margin + idx * (gene_height + gene_spacing)
        terminal_feature = get_terminal_feature(all_features)

        # ラベルを描画
        if show_labels:
            dwg.add(dwg.text(
                label,
                insert=(LEFT_MARGIN, y_pos + height_feature - 2),
                font_size='11px',
                fill='black',
                font_family='monospace'
            ))

        # フィーチャーを描画（ドメイン以外）
        for feat in all_features:
            x_start = LEFT_MARGIN + label_width + (feat.start / shrink_factor + shift / shrink_factor) * scale
            x_end = LEFT_MARGIN + label_width + (feat.end / shrink_factor + shift / shrink_factor) * scale
            width = x_end - x_start

            if feat.feature_type == 'domain':
                continue

            if feat.feature_type == 'deletion':
                # くの字型の折れ線
                y_line = y_pos + height_feature // 2
                mid_x = x_start + (x_end - x_start) / 2
                offset = 10
                dwg.add(
                    dwg.polyline(
                        points=[
                            (x_start, y_line),
                            (mid_x, y_line - offset),
                            (x_end, y_line)
                        ],
                        fill='none',
                        stroke='black',
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
                    tip = height_feature // 2
                    dwg.add(
                        dwg.polygon(
                            points=[
                                (x_start, y_pos),
                                (x_end - tip, y_pos),
                                (x_end, y_pos + height_feature / 2),
                                (x_end - tip, y_pos + height_feature),
                                (x_start, y_pos + height_feature)
                            ],
                            fill=fill_color,
                            stroke=stroke_color if outline_enabled else 'none',
                            stroke_width=stroke_width
                        )
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
            else:
                ins_pos = ins
                ins_length = 1

            x = LEFT_MARGIN + label_width + (ins_pos / shrink_factor + shift / shrink_factor) * scale
            base_width = get_insertion_base_width(ins_length, shrink_factor, scale)

            dwg.add(
                dwg.polygon(
                    points=[
                        (x - base_width / 2, y_triangle),
                        (x + base_width / 2, y_triangle),
                        (x, y_triangle + triangle_height)
                    ],
                    fill="black",
                    stroke="black",
                    stroke_width=1.5
                )
            )

        # === SNPs ===
        snp_extend_up = 8
        snp_extend_down = 8
        y_snp_top = y_pos - snp_extend_up
        y_snp_bottom = y_pos + height_feature + snp_extend_down

        for snp_pos in getattr(gene, "snps", []):
            x = LEFT_MARGIN + label_width + (snp_pos / shrink_factor + shift / shrink_factor) * scale
            dwg.add(
                dwg.line(
                    start=(x, y_snp_top),
                    end=(x, y_snp_bottom),
                    stroke="black",
                    stroke_width=1.2
                )
            )

        # ドメインを描画（上層）
        for feat in all_features:
            if feat.feature_type == 'domain':
                x_start = LEFT_MARGIN + label_width + (feat.start / shrink_factor + shift / shrink_factor) * scale
                x_end = LEFT_MARGIN + label_width + (feat.end / shrink_factor + shift / shrink_factor) * scale
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
        features = gene.get_sorted_features()
        if features:
            gene_start = min(f.start for f in features)
            gene_end = max(f.end for f in features)
        else:
            gene_start = 0
            gene_end = 0
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
    all_starts = [g['start'] for g in gene_ranges if g['start'] > 0]
    all_ends = [g['end'] for g in gene_ranges if g['end'] > 0]

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
    tick_interval, unit_label, divisor = get_tick_params(draw_end - draw_start)
    first_tick = ((draw_start // tick_interval) + 1) * tick_interval

    for tick_pos in range(first_tick, draw_end + 1, tick_interval):
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
        all_features = gene.get_sorted_features()
        y_pos = top_margin + track_idx * (track_height + gene_spacing)
        terminal_feature = get_terminal_feature(all_features)

        # 遺伝子の中心X座標を計算（ラベル配置用）
        gene_center_x = None
        if all_features:
            gene_start = min(f.start for f in all_features)
            gene_end = max(f.end for f in all_features)
            gene_center_x = LEFT_MARGIN + ((gene_start + gene_end) / 2 - draw_start) / shrink_factor * scale

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
                dwg.add(
                    dwg.polyline(
                        points=[
                            (x_start, y_line),
                            (mid_x, y_line - offset),
                            (x_end, y_line)
                        ],
                        fill='none',
                        stroke='black',
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
                    tip = height_feature // 2
                    dwg.add(
                        dwg.polygon(
                            points=[
                                (x_start, y_pos),
                                (x_end - tip, y_pos),
                                (x_end, y_pos + height_feature / 2),
                                (x_end - tip, y_pos + height_feature),
                                (x_start, y_pos + height_feature)
                            ],
                            fill=fill_color,
                            stroke=stroke_color if outline_enabled else 'none',
                            stroke_width=stroke_width
                        )
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
            else:
                ins_pos = ins
                ins_length = 1

            x = LEFT_MARGIN + (ins_pos - draw_start) / shrink_factor * scale
            base_width = get_insertion_base_width(ins_length, shrink_factor, scale)

            dwg.add(
                dwg.polygon(
                    points=[
                        (x - base_width / 2, y_triangle),
                        (x + base_width / 2, y_triangle),
                        (x, y_triangle + triangle_height)
                    ],
                    fill="black",
                    stroke="black",
                    stroke_width=1.5
                )
            )

        # === SNPs ===
        snp_extend_up = 8
        snp_extend_down = 8
        y_snp_top = y_pos - snp_extend_up
        y_snp_bottom = y_pos + height_feature + snp_extend_down

        for snp_pos in getattr(gene, "snps", []):
            x = LEFT_MARGIN + (snp_pos - draw_start) / shrink_factor * scale
            dwg.add(
                dwg.line(
                    start=(x, y_snp_top),
                    end=(x, y_snp_bottom),
                    stroke="black",
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

    legend_x = LEFT_MARGIN + axis_width + 50
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
