#!/usr/bin/env python3
"""Génère les fichiers d'un meuble (modèle 3D, plan de débit, matériaux, notice)
à partir de son fichier `definition.py`.

Usage :
    python scripts/build.py meubles/exemple_etagere
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from atelier import cutlist as cutlist_mod
from atelier import export_3d, export_docs
from atelier.furniture import Furniture


def load_definition(path: pathlib.Path) -> Furniture:
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")
    spec = importlib.util.spec_from_file_location(f"definition_{path.parent.name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "build"):
        raise AttributeError(f"{path} doit définir une fonction build() -> Furniture")
    furniture = module.build()
    if not isinstance(furniture, Furniture):
        raise TypeError(f"build() doit retourner un objet Furniture, reçu {type(furniture)}")
    return furniture


def build_folder(folder: pathlib.Path, force_assemblage: bool = False) -> None:
    definition_path = folder / "definition.py"
    furniture = load_definition(definition_path)

    scene = export_3d.furniture_to_scene(furniture)
    model_path = folder / "model.json"
    model_path.write_text(json.dumps(scene, indent=2, ensure_ascii=False), encoding="utf-8")

    packing = cutlist_mod.pack_furniture(furniture)

    (folder / "cutlist.md").write_text(
        export_docs.render_cutlist_md(furniture, packing), encoding="utf-8"
    )
    (folder / "materiaux.md").write_text(
        export_docs.render_materiaux_md(furniture, packing), encoding="utf-8"
    )

    assemblage_path = folder / "assemblage.md"
    if force_assemblage or not assemblage_path.exists():
        assemblage_path.write_text(export_docs.render_assemblage_md(furniture), encoding="utf-8")

    for material_name, sheets in packing.items():
        svg = export_docs.render_sheets_svg(material_name, sheets)
        safe_name = "".join(c if c.isalnum() else "_" for c in material_name.lower())
        (folder / f"debit_{safe_name}.svg").write_text(svg, encoding="utf-8")

    overall_mm = furniture.overall_size_mm()
    print(f"✓ {furniture.name}")
    print(f"  Encombrement : {overall_mm[0]:.0f} × {overall_mm[1]:.0f} × {overall_mm[2]:.0f} mm")
    print(f"  Coût estimé  : {furniture.total_cost():.2f} €")
    print(f"  Fichiers générés dans {folder}/ : model.json, cutlist.md, materiaux.md, assemblage.md, debit_*.svg")
    rel_model = model_path.resolve().relative_to(REPO_ROOT)
    print(f"  Visualiser : python -m http.server (à la racine du repo), puis ouvrir "
          f"viewer/index.html?model=/{rel_model.as_posix()}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dossier", type=pathlib.Path, help="Dossier du meuble (contenant definition.py)")
    parser.add_argument(
        "--force-assemblage",
        action="store_true",
        help="Régénère aussi assemblage.md (sinon un assemblage.md existant n'est jamais écrasé)",
    )
    args = parser.parse_args()
    build_folder(args.dossier, force_assemblage=args.force_assemblage)


if __name__ == "__main__":
    main()
