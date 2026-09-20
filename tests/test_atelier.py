import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from atelier import Furniture, Hardware, Joint, JointType, Material, Panel
from atelier import contact
from atelier import cutlist as cutlist_mod
from atelier import export_3d
from atelier import hardware_catalog
from atelier import joints as joints_mod

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


class HardwareCatalogTests(unittest.TestCase):
    def test_screw_diameter_scales_with_thickness(self):
        self.assertIn("3.5x", hardware_catalog.recommended_screw(12))
        self.assertIn("4x", hardware_catalog.recommended_screw(18))
        self.assertIn("5x", hardware_catalog.recommended_screw(25))

    def test_screw_length_derived_from_thickness(self):
        # longueur = 2 * épaisseur + 10, arrondie
        self.assertIn("46mm", hardware_catalog.recommended_screw(18))


class JointTests(unittest.TestCase):
    def test_vis_equerre_is_fixed_regardless_of_length(self):
        joint = Joint(panel_a="a", panel_b="b", type=JointType.VIS_EQUERRE, length_mm=9999)
        hw = joint.hardware(thickness_mm=18)
        names = {h.name for h in hw}
        self.assertIn("Équerre de fixation", names)
        self.assertEqual(next(h.qty for h in hw if h.name == "Équerre de fixation"), 1)

    def test_vis_directe_count_scales_with_length(self):
        short = Joint(panel_a="a", panel_b="b", type=JointType.VIS_DIRECTE, length_mm=150)
        long = Joint(panel_a="a", panel_b="b", type=JointType.VIS_DIRECTE, length_mm=1500)
        short_qty = short.hardware(18)[0].qty
        long_qty = long.hardware(18)[0].qty
        self.assertLess(short_qty, long_qty)
        self.assertGreaterEqual(short_qty, 2)  # jamais moins de 2 fixations

    def test_queue_aronde_has_no_hardware_but_uses_glue(self):
        joint = Joint(panel_a="a", panel_b="b", type=JointType.QUEUE_ARONDE, length_mm=300)
        self.assertEqual(joint.hardware(18), [])
        self.assertTrue(joint.uses_glue())

    def test_aggregate_hardware_merges_duplicates_and_adds_one_glue_pot(self):
        j1 = Joint("Côté gauche", "Fond", JointType.TOURILLONS, length_mm=300)
        j2 = Joint("Côté droit", "Fond", JointType.TOURILLONS, length_mm=300)
        thickness = {"Côté gauche": 18, "Côté droit": 18, "Fond": 18}
        hw = joints_mod.aggregate_hardware([j1, j2], thickness)
        dowels = next(h for h in hw if h.name.startswith("Tourillon"))
        glue = [h for h in hw if "Colle" in h.name]
        self.assertEqual(len(glue), 1)  # un seul pot, pas un par joint
        self.assertEqual(glue[0].qty, 1)
        # les tourillons des deux joints sont fusionnés en une seule ligne
        expected_per_joint = joints_mod._fastener_count(300, JointType.TOURILLONS)
        self.assertEqual(dowels.qty, expected_per_joint * 2)

    def test_furniture_all_hardware_includes_joint_hardware(self):
        f = Furniture(name="test")
        f.add_panel(Panel(name="a", length_mm=300, width_mm=300, material=CTP))
        f.add_panel(Panel(name="b", length_mm=300, width_mm=300, material=CTP))
        f.add_hardware(Hardware(name="Poignée", qty=1, unit_price=5.0))
        f.add_joint(Joint("a", "b", JointType.VIS_EQUERRE, length_mm=300))
        names = {h.name for h in f.all_hardware()}
        self.assertIn("Poignée", names)
        self.assertIn("Équerre de fixation", names)
        self.assertGreater(f.total_hardware_cost(), 5.0)  # au moins la poignée + le reste

    def test_render_assembly_steps_references_panel_names(self):
        joints = [Joint("Côté gauche", "Fond", JointType.VIS_DIRECTE, length_mm=300, note="depuis le dessous")]
        steps = joints_mod.render_assembly_steps(joints)
        self.assertEqual(len(steps), 1)
        self.assertIn("Côté gauche", steps[0])
        self.assertIn("Fond", steps[0])
        self.assertIn("depuis le dessous", steps[0])


class ContactGeometryTests(unittest.TestCase):
    """Deux panneaux réellement accolés (comme dans un definition.py correct) :
    un côté vertical (18mm d'épaisseur) posé sur un fond horizontal (16mm),
    qui se touchent exactement au niveau y=71.
    """

    def setUp(self):
        # Fond : 960 (X) x 780 (Z), épaisseur 16mm, centré à y=63 (touche le côté à y=71).
        self.aabb_fond = contact.aabb_mm((0.0, 63.0, 390.0), (960.0, 780.0, 16.0), (90, 0, 0))
        # Côté gauche : 200 (hauteur, Y) x 780 (profondeur, Z), épaisseur 16mm.
        self.aabb_cote = contact.aabb_mm((-472.0, 171.0, 390.0), (200.0, 780.0, 16.0), (90, 0, 90))

    def test_fasteners_protrude_past_panel_a_outer_face_not_on_the_seam(self):
        # aabb_fond = panel_a (traversé par la vis) : épaisseur Y = [55, 71].
        # Le côté touche Fond par le dessus (y=71) donc la face extérieure de
        # Fond est en dessous (y=55) : les fixations doivent dépasser
        # légèrement au-delà (y < 55), ni sur le plan de contact (71),
        # ni juste au centre de l'épaisseur (63).
        fasteners = contact.contact_fasteners_mm(self.aabb_fond, self.aabb_cote, count=6)
        self.assertEqual(len(fasteners), 6)
        for f in fasteners:
            self.assertLess(f.position_mm[1], 55.0)
            self.assertAlmostEqual(f.normal, (0.0, -1.0, 0.0))

    def test_fasteners_spread_along_the_joint_length(self):
        fasteners = contact.contact_fasteners_mm(self.aabb_fond, self.aabb_cote, count=5)
        zs = sorted(f.position_mm[2] for f in fasteners)
        self.assertGreater(zs[-1] - zs[0], 500)  # réparties sur l'essentiel des 780mm de profondeur

    def test_single_fastener_is_centered(self):
        fasteners = contact.contact_fasteners_mm(self.aabb_fond, self.aabb_cote, count=1)
        self.assertEqual(len(fasteners), 1)

    def test_disjoint_boxes_do_not_crash(self):
        far_away = contact.aabb_mm((5000.0, 5000.0, 5000.0), (10.0, 10.0, 10.0), (0, 0, 0))
        fasteners = contact.contact_fasteners_mm(self.aabb_fond, far_away, count=3)
        self.assertEqual(len(fasteners), 3)  # pas d'exception, juste une approximation dégénérée


class Export3DHardwarePositionsTests(unittest.TestCase):
    def test_joint_hardware_marker_count_matches_qty(self):
        f = Furniture(name="test")
        f.add_panel(Panel(name="Fond", length_mm=960, width_mm=780, material=CTP,
                           position_mm=(0.0, 8.0, 390.0), rotation_deg=(90, 0, 0)))
        f.add_panel(Panel(name="Côté gauche", length_mm=200, width_mm=780, material=CTP,
                           position_mm=(-472.0, 116.0, 390.0), rotation_deg=(90, 0, 90)))
        f.add_joint(Joint("Fond", "Côté gauche", JointType.VIS_DIRECTE, length_mm=780))
        scene = export_3d.furniture_to_scene(f)
        vis = next(h for h in scene["hardware"] if h["name"].startswith("Vis à bois"))
        self.assertEqual(len(vis["positions_m"]), vis["qty"])
        self.assertEqual(len(vis["normals"]), vis["qty"])
        self.assertEqual(set(vis["panels"]), {"Fond", "Côté gauche"})

    def test_manual_hardware_positions_pass_through(self):
        f = Furniture(name="test")
        f.add_panel(Panel(name="p", length_mm=100, width_mm=100, material=CTP))
        f.add_hardware(Hardware(name="Poignée", qty=1, unit_price=5.0, positions_mm=[(10.0, 20.0, 30.0)]))
        scene = export_3d.furniture_to_scene(f)
        poignee = next(h for h in scene["hardware"] if h["name"] == "Poignée")
        self.assertEqual(poignee["positions_m"], [[0.01, 0.02, 0.03]])

    def test_hardware_without_position_has_empty_list(self):
        f = Furniture(name="test")
        f.add_panel(Panel(name="p", length_mm=100, width_mm=100, material=CTP))
        f.add_hardware(Hardware(name="Colle", qty=1, unit_price=5.0))
        scene = export_3d.furniture_to_scene(f)
        colle = next(h for h in scene["hardware"] if h["name"] == "Colle")
        self.assertEqual(colle["positions_m"], [])
        self.assertEqual(colle["panels"], [])

    def test_joint_with_unknown_panel_raises_clear_error(self):
        f = Furniture(name="test")
        f.add_panel(Panel(name="Fond", length_mm=960, width_mm=780, material=CTP))
        f.add_joint(Joint("Fond", "Panneau introuvable", JointType.VIS_DIRECTE, length_mm=300))
        with self.assertRaises(ValueError):
            export_3d.furniture_to_scene(f)


if __name__ == "__main__":
    unittest.main()
