
import sys
from pathlib import Path

# Add current directory and api directory to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "api"))

from api.models import GeneStructure, GeneFeature
from api.drawer import draw_gene_structure

class MockDwg:
    def __init__(self, *args, **kwargs):
        self.elements = []
    def tostring(self):
        return self
    def add(self, element):
        self.elements.append(element)
    def line(self, *args, **kwargs):
        return ("line", args, kwargs)
    def text(self, text, *args, **kwargs):
        return ("text", text, args, kwargs)
    def rect(self, *args, **kwargs):
        return ("rect", args, kwargs)
    def polygon(self, *args, **kwargs):
        return ("polygon", args, kwargs)
    def path(self, *args, **kwargs):
        return ("path", args, kwargs)

import svgwrite
svgwrite.Drawing = MockDwg

def test_relative_scale_bar():
    gene = GeneStructure("test", "chr1", "+")
    # Gene from 1000 to 2000
    gene.add_feature(GeneFeature("chr1", 1000, 2000, "exon", "+"))
    
    # In relative mode, this will be shifted to 1 to 1001
    print("Before to_relative:", gene.get_full_extent())
    
    # We use draw_gene_structure which calls to_relative() internally
    # But wait, it calls it and uses the shifted coordinates for drawing.
    
    # mock get_tick_params to return predictable values
    import api.drawer
    original_get_tick_params = api.drawer.get_tick_params
    api.drawer.get_tick_params = lambda range_bp, shrink_factor, scale: (500, "bp", 1)
    
    dwg = draw_gene_structure(gene, coordinate_mode="relative")
    
    print("\nRelative Mode Scale Bar Ticks:")
    for el in dwg.elements:
        if isinstance(el, tuple) and el[0] == "text":
            print(f"Label: {el[1]}, Position: {el[3].get('insert')}")

    # Current logic reproduction (already done above)
    
    # Proposed fix reproduction
    print("\n--- Proposed Fix ---")
    def proposed_draw_gene_structure(gene, coordinate_mode="relative", anchor=0):
        # Mocking the proposed changes in api/drawer.py
        gene.to_relative()
        actual_min_start, actual_max_end = gene.get_full_extent()
        tick_interval = 500
        shrink_factor = 30.0
        scale = 2.0
        
        # Proposed change 1: shift = -actual_min_start
        shift = -actual_min_start
        
        LEFT_MARGIN = 50
        axis_y = 100
        
        dwg = MockDwg()
        
        x_axis_start = LEFT_MARGIN + (actual_min_start / shrink_factor + shift / shrink_factor) * scale
        print(f"x_axis_start: {x_axis_start}")
        
        display_start = anchor if coordinate_mode == "absolute" else 0
        first_tick = (actual_min_start // tick_interval) * tick_interval
        
        for tick_val in range(first_tick, actual_max_end + 1, tick_interval):
            if tick_val < actual_min_start - tick_interval / 10:
                continue
            
            x = LEFT_MARGIN + (tick_val / shrink_factor + shift / shrink_factor) * scale
            
            # Proposed change 2: display_tick_val = display_start + tick_val - 1 (for both)
            display_tick_val = display_start + tick_val - 1
            
            print(f"Label: {display_tick_val}, Position: {x}")
            dwg.add(("text", display_tick_val, None, {"insert": (x, axis_y)}))
        
        return dwg

    gene_fix = GeneStructure("test_fix", "chr1", "+")
    gene_fix.add_feature(GeneFeature("chr1", 1000, 2000, "exon", "+"))
    proposed_draw_gene_structure(gene_fix, coordinate_mode="relative")

if __name__ == "__main__":
    test_relative_scale_bar()
