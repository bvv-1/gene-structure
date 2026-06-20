import svgwrite

from api.drawer import draw_terminal_feature, get_terminal_feature
from api.models import GeneFeature


def test_get_terminal_feature_uses_rightmost_feature_on_plus_strand():
    features = [
        GeneFeature("chr1", 1, 100, "CDS", "+"),
        GeneFeature("chr1", 300, 500, "CDS", "+"),
    ]

    terminal = get_terminal_feature(features, "+")

    assert terminal.start == 300
    assert terminal.end == 500


def test_get_terminal_feature_uses_leftmost_feature_on_minus_strand():
    features = [
        GeneFeature("chr1", 1, 100, "CDS", "-"),
        GeneFeature("chr1", 300, 500, "CDS", "-"),
    ]

    terminal = get_terminal_feature(features, "-")

    assert terminal.start == 1
    assert terminal.end == 100


def test_draw_terminal_feature_points_left_on_minus_strand():
    dwg = svgwrite.Drawing(size=(200, 80))

    draw_terminal_feature(
        dwg,
        x_start=20,
        x_end=120,
        y_pos=10,
        height_feature=15,
        fill_color="lightblue",
        stroke_color="black",
        outline_enabled=True,
        stroke_width=1,
        strand="-",
    )

    svg = dwg.tostring()

    assert "20,17.5" in svg
    assert "120,10" in svg
    assert "120,25" in svg
    assert "120,17.5" not in svg
