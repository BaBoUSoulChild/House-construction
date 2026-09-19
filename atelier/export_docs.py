from __future__ import annotations

from . import cutlist as cutlist_mod
from . import joints as joints_mod
from .furniture import Furniture


def render_cutlist_md(furniture: Furniture, packing: dict[str, list[cutlist_mod.Sheet]]) -> str:
    lines = [f"# Plan de débit — {furniture.name}", ""]

    lines.append("## Liste des panneaux")
    lines.append("")
    lines.append("| Panneau | Matériau | Longueur (mm) | Largeur (mm) | Épaisseur (mm) | Surface (m²) |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for p in furniture.panels:
        lines.append(
            f"| {p.name} | {p.material.name} | {p.length_mm:.0f} | {p.width_mm:.0f} "
            f"| {p.thickness_mm:.0f} | {p.area_m2:.3f} |"
        )
    lines.append("")

    lines.append("## Regroupement (quantités)")
    lines.append("")
    lines.append("| Matériau | Longueur (mm) | Largeur (mm) | Épaisseur (mm) | Quantité |")
    lines.append("|---|---:|---:|---:|---:|")
    for (mat, length, width, thickness), qty in sorted(cutlist_mod.group_panels(furniture).items()):
        lines.append(f"| {mat} | {length:.0f} | {width:.0f} | {thickness:.0f} | {qty} |")
    lines.append("")

    lines.append("## Optimisation de découpe (nesting)")
    lines.append("")
    lines.append(
        "Heuristique glouton (shelf packing, premier ajustement décroissant). "
        "Voir les fichiers `debit_*.svg` pour le plan visuel de chaque plaque."
    )
    lines.append("")
    lines.append("| Matériau | Plaques nécessaires | Taux d'utilisation moyen |")
    lines.append("|---|---:|---:|")
    for material_name, sheets in packing.items():
        if not sheets:
            continue
        avg_util = sum(s.utilization() for s in sheets) / len(sheets)
        lines.append(f"| {material_name} | {len(sheets)} | {avg_util * 100:.0f}% |")
    lines.append("")

    return "\n".join(lines)


def render_materiaux_md(furniture: Furniture, packing: dict[str, list[cutlist_mod.Sheet]]) -> str:
    lines = [f"# Matériaux & coût — {furniture.name}", ""]

    lines.append("## Panneaux")
    lines.append("")
    lines.append("| Matériau | Plaques nécessaires | Prix / m² | Coût estimé |")
    lines.append("|---|---:|---:|---:|")
    materials_seen = {}
    for p in furniture.panels:
        materials_seen[p.material.name] = p.material
    for name, material in sorted(materials_seen.items()):
        n_sheets = len(packing.get(name, []))
        sheet_area_m2 = (material.sheet_length_mm * material.sheet_width_mm) / 1_000_000
        cost = n_sheets * sheet_area_m2 * material.price_per_m2
        lines.append(f"| {name} | {n_sheets} | {material.price_per_m2:.2f} € | {cost:.2f} € |")
    lines.append("")

    lines.append("## Quincaillerie")
    lines.append("")
    all_hardware = furniture.all_hardware()
    if all_hardware:
        lines.append("| Élément | Quantité | Prix unitaire | Total | Note |")
        lines.append("|---|---:|---:|---:|---|")
        for h in all_hardware:
            lines.append(f"| {h.name} | {h.qty} | {h.unit_price:.2f} € | {h.total_price:.2f} € | {h.note} |")
        if furniture.joints:
            lines.append("")
            lines.append(
                f"_{len(furniture.joints)} assemblage(s) définis dans `definition.py` — la quincaillerie "
                "qu'ils nécessitent (vis, équerres, tourillons...) est calculée automatiquement et "
                "incluse ci-dessus._"
            )
    else:
        lines.append("_Aucune quincaillerie renseignée._")
    lines.append("")

    lines.append("## Total")
    lines.append("")
    lines.append(f"- Bois (au m² découpé) : **{furniture.total_wood_cost():.2f} €**")
    lines.append(f"- Quincaillerie : **{furniture.total_hardware_cost():.2f} €**")
    lines.append(f"- **Total estimé : {furniture.total_cost():.2f} €**")
    lines.append("")
    lines.append(
        "_Note : le coût \"bois\" ci-dessus est calculé au m² réellement découpé ; "
        "le coût par plaque entière (section Panneaux) est une meilleure estimation "
        "de ce qu'il faudra acheter en magasin._"
    )
    lines.append("")

    return "\n".join(lines)


def render_assemblage_md(furniture: Furniture) -> str:
    lines = [f"# Notice de montage — {furniture.name}", ""]
    if furniture.description:
        lines.append(furniture.description)
        lines.append("")
    lines.append("## Pièces")
    lines.append("")
    for p in furniture.panels:
        note = f" — {p.note}" if p.note else ""
        lines.append(f"- **{p.name}** ({p.length_mm:.0f} × {p.width_mm:.0f} × {p.thickness_mm:.0f} mm){note}")
    lines.append("")
    lines.append("## Quincaillerie")
    lines.append("")
    for h in furniture.all_hardware():
        lines.append(f"- {h.name} × {h.qty}" + (f" — {h.note}" if h.note else ""))
    lines.append("")
    lines.append("## Étapes")
    lines.append("")
    if furniture.joints:
        lines.append(
            "_Généré depuis les assemblages (`Joint`) définis dans `definition.py`, "
            "dans l'ordre où ils y sont déclarés. Ajustez librement ce fichier ensuite : "
            "il n'est jamais régénéré automatiquement une fois créé._"
        )
        lines.append("")
        lines.extend(joints_mod.render_assembly_steps(furniture.joints))
    else:
        lines.append("<!-- À compléter : décrire ici l'ordre d'assemblage, les perçages, etc. -->")
    lines.append("")
    return "\n".join(lines)


def render_sheets_svg(material_name: str, sheets: list[cutlist_mod.Sheet]) -> str:
    """Un SVG par matériau, montrant chaque plaque empilée verticalement."""
    if not sheets:
        return ""
    scale = 0.2  # px per mm
    margin = 20
    sheet_w = sheets[0].length_mm * scale
    sheet_h = sheets[0].width_mm * scale
    total_h = len(sheets) * (sheet_h + margin) + margin
    total_w = sheet_w + 2 * margin

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w:.0f}" height="{total_h:.0f}" '
        f'viewBox="0 0 {total_w:.0f} {total_h:.0f}" font-family="sans-serif">',
        f'<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{margin}" y="14" font-size="13" font-weight="bold">{material_name}</text>',
    ]
    for i, sheet in enumerate(sheets):
        oy = margin + i * (sheet_h + margin) + 10
        ox = margin
        parts.append(
            f'<rect x="{ox:.1f}" y="{oy:.1f}" width="{sheet_w:.1f}" height="{sheet_h:.1f}" '
            f'fill="none" stroke="black" stroke-width="1.5"/>'
        )
        parts.append(
            f'<text x="{ox:.1f}" y="{oy - 3:.1f}" font-size="10">'
            f'Plaque {i + 1} — utilisation {sheet.utilization() * 100:.0f}%</text>'
        )
        for placement in sheet.placements:
            px = ox + placement.x_mm * scale
            py = oy + placement.y_mm * scale
            pw = placement.length_mm * scale
            ph = placement.width_mm * scale
            parts.append(
                f'<rect x="{px:.1f}" y="{py:.1f}" width="{pw:.1f}" height="{ph:.1f}" '
                f'fill="#c9a87655" stroke="#555" stroke-width="1"/>'
            )
            label = placement.panel_name + (" (pivoté)" if placement.rotated else "")
            parts.append(
                f'<text x="{px + 3:.1f}" y="{py + 12:.1f}" font-size="9">{label}</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts)
