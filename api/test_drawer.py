import unittest

import svgwrite

from api.drawer import draw_region_gene_structures, draw_terminal_feature, get_terminal_feature, get_tick_params
from api.models import GeneFeature, GeneStructure


class DrawerTest(unittest.TestCase):
    def test_get_terminal_feature_uses_rightmost_feature_on_plus_strand(self):
        features = [
            GeneFeature("chr1", 1, 100, "CDS", "+"),
            GeneFeature("chr1", 300, 500, "CDS", "+"),
        ]

        terminal = get_terminal_feature(features, "+")

        self.assertEqual(terminal.start, 300)
        self.assertEqual(terminal.end, 500)

    def test_get_terminal_feature_uses_leftmost_feature_on_minus_strand(self):
        features = [
            GeneFeature("chr1", 1, 100, "CDS", "-"),
            GeneFeature("chr1", 300, 500, "CDS", "-"),
        ]

        terminal = get_terminal_feature(features, "-")

        self.assertEqual(terminal.start, 1)
        self.assertEqual(terminal.end, 100)

    def test_draw_terminal_feature_points_left_on_minus_strand(self):
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

        self.assertIn("20,17.5", svg)
        self.assertIn("120,10", svg)
        self.assertIn("120,25", svg)
        self.assertNotIn("120,17.5", svg)

    def test_get_tick_params_does_not_relax_below_minimum_label_spacing(self):
        tick_interval, unit_label, divisor = get_tick_params(
            range_size=2400,
            shrink_factor=30.0,
            scale=2.0,
        )

        self.assertEqual(tick_interval, 1000)
        self.assertEqual(unit_label, "kb")
        self.assertEqual(divisor, 1000)

    def test_region_baseline_is_limited_to_each_gene_extent(self):
        left_gene = GeneStructure("region-left", "chr1", "+")
        left_gene.add_feature(GeneFeature("chr1", 1000, 1079, "five_prime_UTR", "+"))
        left_gene.add_feature(GeneFeature("chr1", 1080, 1150, "CDS", "+"))
        left_gene.add_feature(GeneFeature("chr1", 1151, 1499, "intron", "+"))
        left_gene.add_feature(GeneFeature("chr1", 1500, 1750, "CDS", "+"))
        left_gene.add_feature(GeneFeature("chr1", 1751, 1900, "three_prime_UTR", "+"))

        right_gene = GeneStructure("region-right", "chr1", "-")
        right_gene.add_feature(GeneFeature("chr1", 2300, 2449, "five_prime_UTR", "-"))
        right_gene.add_feature(GeneFeature("chr1", 2450, 2600, "CDS", "-"))
        right_gene.add_feature(GeneFeature("chr1", 2601, 2899, "intron", "-"))
        right_gene.add_feature(GeneFeature("chr1", 2900, 3080, "CDS", "-"))
        right_gene.add_feature(GeneFeature("chr1", 3081, 3200, "three_prime_UTR", "-"))

        svg = draw_region_gene_structures(
            genes=[left_gene, right_gene],
            labels=["region-left", "region-right"],
            region_start=900,
            region_end=3300,
            line_color="#222222",
        )

        self.assertIn(
            'stroke="#222222" stroke-width="1" x1="56.666666666666664" x2="116.66666666666667" y1="57" y2="57"',
            svg,
        )
        self.assertIn(
            'stroke="#222222" stroke-width="1" x1="143.33333333333331" x2="203.33333333333334" y1="147" y2="147"',
            svg,
        )
        self.assertNotIn(
            'stroke="#222222" stroke-width="1" x1="50.0" x2="210.0" y1="57" y2="57"',
            svg,
        )
        self.assertNotIn(
            'stroke="#222222" stroke-width="1" x1="50.0" x2="210.0" y1="147" y2="147"',
            svg,
        )


if __name__ == "__main__":
    unittest.main()
