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

def draw_gene_structure(gene: GeneStructure, scale=2, extra_padding=100, shrink_factor=30.0,
                        utr_color=None, exon_color=None, line_color=None, domain_color=None):
    # デフォルト色を設定
    utr_color = utr_color or DEFAULT_COLORS['utr_color']
    exon_color = exon_color or DEFAULT_COLORS['exon_color']
    line_color = line_color or DEFAULT_COLORS['line_color']
    domain_color = domain_color or DEFAULT_COLORS['domain_color']

    min_start = gene.to_relative()
    all_features = gene.get_sorted_features()
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
            dwg.add(
                dwg.rect(
                    insert=(x_start, y_pos),
                    size=(width, height_feature),
                    fill='none',
                    stroke='red',
                    stroke_dasharray="5,5",
                    stroke_width=2
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

    for feat in all_features:
        if feat.feature_type == 'domain':
            x_start = LEFT_MARGIN + (feat.start / shrink_factor + shift / shrink_factor) * scale
            x_end = LEFT_MARGIN + (feat.end / shrink_factor + shift / shrink_factor) * scale
            width = x_end - x_start

            dwg.add(
                dwg.rect(
                    insert=(x_start, y_pos),
                    size=(width, height_feature),
                    fill=domain_color,
                    stroke=FEATURE_OUTLINES.get('domain', 'black'),
                    stroke_width=FEATURE_OUTLINE_WIDTHS.get('domain', 1)
                )
            )

    # === 凡例 ===
    legend_x = max_x_coord + 100
    legend_y = 30
    box_size = 12
    spacing = 20
    legend_items = [
        ('domain', 'Domain', domain_color),
        ('CDS', 'Exon/CDS', exon_color),
        ('five_prime_UTR', "5' UTR", utr_color),
        ('three_prime_UTR', "3' UTR", utr_color),
        ('intron', 'Intron', line_color),
        ('deletion', 'Deletion', None)
    ]
    for i, (feat_key, label, color) in enumerate(legend_items):
        y_legend = legend_y + i * spacing
        if feat_key == 'deletion':
            dwg.add(dwg.rect(
                insert=(legend_x, y_legend),
                size=(box_size, box_size),
                fill='none',
                stroke='red',
                stroke_dasharray="5,5",
                stroke_width=2
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
                dwg.add(
                    dwg.rect(
                        insert=(x_start, y_pos),
                        size=(width, height_feature),
                        fill='none',
                        stroke='red',
                        stroke_dasharray="5,5",
                        stroke_width=2
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

        # ドメインを描画（上層）
        for feat in all_features:
            if feat.feature_type == 'domain':
                x_start = LEFT_MARGIN + label_width + (feat.start / shrink_factor + shift / shrink_factor) * scale
                x_end = LEFT_MARGIN + label_width + (feat.end / shrink_factor + shift / shrink_factor) * scale
                width = x_end - x_start

                dwg.add(
                    dwg.rect(
                        insert=(x_start, y_pos),
                        size=(width, height_feature),
                        fill=domain_color,
                        stroke=FEATURE_OUTLINES.get('domain', 'black'),
                        stroke_width=FEATURE_OUTLINE_WIDTHS.get('domain', 1)
                    )
                )

    # === 凡例（右上に1つだけ配置） ===
    legend_x = global_max_x + 50
    legend_y = 30
    box_size = 12
    spacing = 20
    legend_items = [
        ('domain', 'Domain', domain_color),
        ('CDS', 'Exon/CDS', exon_color),
        ('five_prime_UTR', "5' UTR", utr_color),
        ('three_prime_UTR', "3' UTR", utr_color),
        ('intron', 'Intron', line_color),
        ('deletion', 'Deletion', None)
    ]
    for i, (feat_key, label_text, color) in enumerate(legend_items):
        y_legend = legend_y + i * spacing
        if feat_key == 'deletion':
            dwg.add(dwg.rect(
                insert=(legend_x, y_legend),
                size=(box_size, box_size),
                fill='none',
                stroke='red',
                stroke_dasharray="5,5",
                stroke_width=2
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

    Args:
        genes: 描画するGeneStructureのリスト
        labels: 各遺伝子のラベル
        region_start: 表示領域の開始座標（ゲノム座標）
        region_end: 表示領域の終了座標（ゲノム座標）
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

    height_feature = 15

    # ラベルの最大文字数に基づいて基本幅を計算
    max_label_len = max(len(label) for label in labels) if labels else 0
    label_base_width = int(max_label_len * 6.6) + 5
    label_width = (label_base_width + label_spacing) if show_labels else 0

    # 全遺伝子の座標範囲を計算（はみ出しを含む）
    all_starts = []
    all_ends = []
    for gene in genes:
        for feat in gene.get_sorted_features():
            all_starts.append(feat.start)
            all_ends.append(feat.end)

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
    canvas_width = LEFT_MARGIN + label_width + axis_width + extra_padding + 300

    # Canvas高さ
    gene_height = height_feature + 10
    top_margin = 50  # 座標軸用のスペース
    canvas_height = top_margin + len(genes) * (gene_height + gene_spacing) + 150

    # メモリ上にSVGを作成
    dwg = svgwrite.Drawing(size=(canvas_width, canvas_height))

    # 座標軸を描画（上部）
    axis_y = top_margin - 20
    dwg.add(dwg.line(
        start=(label_width + LEFT_MARGIN, axis_y),
        end=(label_width + LEFT_MARGIN + axis_width, axis_y),
        stroke='black',
        stroke_width=1
    ))

    # 目盛りを描画
    tick_interval, unit_label, divisor = get_tick_params(draw_end - draw_start)
    first_tick = ((draw_start // tick_interval) + 1) * tick_interval

    for tick_pos in range(first_tick, draw_end + 1, tick_interval):
        x = label_width + LEFT_MARGIN + (tick_pos - draw_start) / shrink_factor * scale

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
    for idx, (gene, label) in enumerate(zip(genes, labels)):
        all_features = gene.get_sorted_features()
        y_pos = top_margin + idx * (gene_height + gene_spacing)

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
            # X座標 = 描画範囲の開始位置からのオフセット
            x_start = label_width + LEFT_MARGIN + (feat.start - draw_start) / shrink_factor * scale
            x_end = label_width + LEFT_MARGIN + (feat.end - draw_start) / shrink_factor * scale
            width = x_end - x_start

            if feat.feature_type == 'domain':
                continue

            if feat.feature_type == 'deletion':
                dwg.add(
                    dwg.rect(
                        insert=(x_start, y_pos),
                        size=(width, height_feature),
                        fill='none',
                        stroke='red',
                        stroke_dasharray="5,5",
                        stroke_width=2
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

        # ドメインを描画（上層）
        for feat in all_features:
            if feat.feature_type == 'domain':
                x_start = label_width + LEFT_MARGIN + (feat.start - draw_start) / shrink_factor * scale
                x_end = label_width + LEFT_MARGIN + (feat.end - draw_start) / shrink_factor * scale
                width = x_end - x_start

                dwg.add(
                    dwg.rect(
                        insert=(x_start, y_pos),
                        size=(width, height_feature),
                        fill=domain_color,
                        stroke=FEATURE_OUTLINES.get('domain', 'black'),
                        stroke_width=FEATURE_OUTLINE_WIDTHS.get('domain', 1)
                    )
                )

    # === 凡例（右上に1つだけ配置） ===
    legend_x = label_width + LEFT_MARGIN + axis_width + 50
    legend_y = 30
    box_size = 12
    spacing = 20
    legend_items = [
        ('domain', 'Domain', domain_color),
        ('CDS', 'Exon/CDS', exon_color),
        ('five_prime_UTR', "5' UTR", utr_color),
        ('three_prime_UTR', "3' UTR", utr_color),
        ('intron', 'Intron', line_color),
        ('deletion', 'Deletion', None)
    ]
    for i, (feat_key, label_text, color) in enumerate(legend_items):
        y_legend = legend_y + i * spacing
        if feat_key == 'deletion':
            dwg.add(dwg.rect(
                insert=(legend_x, y_legend),
                size=(box_size, box_size),
                fill='none',
                stroke='red',
                stroke_dasharray="5,5",
                stroke_width=2
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
