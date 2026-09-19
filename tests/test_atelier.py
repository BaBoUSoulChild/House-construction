import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from atelier import Furniture, Hardware, Material, Panel
from atelier import cutlist as cutlist_mod
from atelier import export_3d

CTP = Material(name="CTP18", thickness_mm=18.0, price_per_m2=30.0)


class BoundingBoxTests(unittest.TestCase):
    def test_axis_aligned_single_panel(self):
        f = Furniture(name="test")
        f.add_panel(Panel(name="p", length_mm=800, width_mm=300, material=CTP, position_mm=(0, 0, 0)))
        lo, hi = f.bounding_box_mm()
        self.assertAlmostEqual(hi[0] - lo[0], 800, places=6)
        self.assertAlmostEqual(hi[1] - lo[1], 300, places=6)
        self.assertAlmostEqual(hi[2] - lo[2], 18, places=6)

    def test_side_panel_rotation_swaps_extents(self):
        # rotation (90, 0, 90) doit mettre length_mm sur Y et thickness sur X,
        # comme utilisé pour les côtés de l'étagère d'exemple.
        f = Furniture(name="test")
        f.add_panel(
            Panel(
                name="cote",
                length_mm=1800,
                width_mm=300,
                material=CTP,
                position_mm=(0, 900, 150),
                rotation_deg=(90, 0, 90),
            )
        )
        overall = f.overall_size_mm()
        self.assertAlmostEqual(overall[0], 18, places=6)
        self.assertAlmostEqual(overall[1], 1800, places=6)
        self.assertAlmostEqual(overall[2], 300, places=6)

    def test_empty_furniture(self):
        f = Furniture(name="vide")
        lo, hi = f.bounding_box_mm()
        self.assertEqual(lo, hi)


class CostTests(unittest.TestCase):
    def test_wood_and_hardware_cost(self):
        f = Furniture(name="test")
        f.add_panel(Panel(name="p", length_mm=1000, width_mm=500, material=CTP))  # 0.5 m2
        f.add_hardware(Hardware(name="vis", qty=10, unit_price=0.1))
        self.assertAlmostEqual(f.total_wood_cost(), 0.5 * 30.0, places=6)
        self.assertAlmostEqual(f.total_hardware_cost(), 1.0, places=6)
        self.assertAlmostEqual(f.total_cost(), 16.0, places=6)


class CutlistTests(unittest.TestCase):
    def test_grouping_counts_identical_panels(self):
        f = Furniture(name="test")
        for _ in range(3):
            f.add_panel(Panel(name="tablette", length_mm=764, width_mm=300, material=CTP))
        groups = cutlist_mod.group_panels(f)
        self.assertEqual(groups[("CTP18", 764, 300, 18)], 3)

    def test_packing_places_every_panel_without_overlap_area(self):
        f = Furniture(name="test")
        panels = [
            Panel(name=f"p{i}", length_mm=800, width_mm=400, material=CTP) for i in range(6)
        ]
        for p in panels:
            f.add_panel(p)
        packing = cutlist_mod.pack_furniture(f)
        sheets = packing["CTP18"]
        total_placements = sum(len(s.placements) for s in sheets)
        self.assertEqual(total_placements, 6)
        for sheet in sheets:
            self.assertLessEqual(sheet.utilization(), 1.0)

    def test_panel_too_big_for_sheet_raises(self):
        # Un panneau plus grand que la plaque doit être signalé, jamais disparaître
        # silencieusement du plan de débit.
        huge = Material(name="petit", thickness_mm=18.0, price_per_m2=10.0,
                         sheet_length_mm=1000.0, sheet_width_mm=1000.0)
        f = Furniture(name="test")
        f.add_panel(Panel(name="trop_grand", length_mm=2000, width_mm=2000, material=huge))
        with self.assertRaises(ValueError):
            cutlist_mod.pack_furniture(f)


class Export3DTests(unittest.TestCase):
    def test_scene_units_are_converted_to_meters(self):
        f = Furniture(name="Meuble")
        f.add_panel(Panel(name="p", length_mm=800, width_mm=300, material=CTP, position_mm=(100, 200, 9)))
        scene = export_3d.furniture_to_scene(f)
        panel = scene["panels"][0]
        self.assertAlmostEqual(panel["size_m"][0], 0.8, places=6)
        self.assertAlmostEqual(panel["position_m"][0], 0.1, places=6)
        self.assertEqual(scene["unit"], "m")


if __name__ == "__main__":
    unittest.main()
