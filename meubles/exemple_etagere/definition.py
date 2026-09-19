"""Étagère murale, 3 tablettes — meuble d'exemple pour valider le pipeline complet.

Convention d'axes (comme three.js) : Y = hauteur, X/Z = plan horizontal.
Origine : centre en X, sol en Y=0, profondeur de 0 (arrière) à D (avant).

Pour construire un meuble : copier ce dossier, adapter les cotes ci-dessous,
puis lancer `python scripts/build.py meubles/<votre_dossier>`.
"""

from atelier import Furniture, Hardware, Material, Panel

# --- Cotes générales (mm) ---------------------------------------------------

LARGEUR = 800.0
HAUTEUR = 1800.0
PROFONDEUR = 300.0

CTP = Material(name="Contreplaqué 18mm", thickness_mm=18.0, price_per_m2=32.0, color="#c9a876")
FOND = Material(name="Fond dur 4mm", thickness_mm=4.0, price_per_m2=9.0, color="#e8dcc0")


def build() -> Furniture:
    f = Furniture(
        name="Étagère murale 3 tablettes",
        description="Étagère murale en contreplaqué 18mm, 800 x 1800 x 300mm, fond en dur 4mm.",
    )

    demi_largeur = LARGEUR / 2
    x_cote = demi_largeur - CTP.thickness_mm / 2

    # Côtés (panneaux verticaux) : la longueur (1800) devient la hauteur,
    # la largeur (300) devient la profondeur, l'épaisseur (18) reste horizontale.
    for nom, signe in (("Côté gauche", -1), ("Côté droit", 1)):
        f.add_panel(
            Panel(
                name=nom,
                length_mm=HAUTEUR,
                width_mm=PROFONDEUR,
                material=CTP,
                position_mm=(signe * x_cote, HAUTEUR / 2, PROFONDEUR / 2),
                rotation_deg=(90, 0, 90),
            )
        )

    # Tablettes horizontales, encastrées entre les deux côtés.
    largeur_tablette = LARGEUR - 2 * CTP.thickness_mm
    for nom, y in (
        ("Tablette basse", CTP.thickness_mm / 2),
        ("Tablette médiane", HAUTEUR / 2),
        ("Tablette haute", HAUTEUR - CTP.thickness_mm / 2),
    ):
        f.add_panel(
            Panel(
                name=nom,
                length_mm=largeur_tablette,
                width_mm=PROFONDEUR,
                material=CTP,
                position_mm=(0.0, y, PROFONDEUR / 2),
                rotation_deg=(90, 0, 0),
            )
        )

    # Fond en dur, pour la rigidité et la fixation murale.
    f.add_panel(
        Panel(
            name="Fond",
            length_mm=LARGEUR,
            width_mm=HAUTEUR,
            material=FOND,
            position_mm=(0.0, HAUTEUR / 2, FOND.thickness_mm / 2),
            rotation_deg=(0, 0, 0),
            note="Cloué/collé sur les côtés et les tablettes.",
        )
    )

    f.add_hardware(Hardware(name="Vis à bois 4x40mm", qty=12, unit_price=0.05, note="Fixation tablettes/côtés"))
    f.add_hardware(Hardware(name="Pointes 15mm", qty=24, unit_price=0.02, note="Fixation du fond"))
    f.add_hardware(Hardware(name="Équerre de fixation murale", qty=2, unit_price=3.5, note="Accroche murale"))

    return f
