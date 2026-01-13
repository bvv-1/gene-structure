import io
import svgwrite

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
