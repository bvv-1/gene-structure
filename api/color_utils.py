# =====================
# カラーユーティリティ関数
# =====================


def get_domain_color(domain_name, color_map, palette):
    """
    domain名ごとに一貫した色を返す

    Args:
        domain_name: ドメイン名
        color_map: ドメイン名→色のマッピング辞書
        palette: 色パレットリスト

    Returns:
        割り当てられた色
    """
    if domain_name not in color_map:
        color_map[domain_name] = palette[len(color_map) % len(palette)]
    return color_map[domain_name]
