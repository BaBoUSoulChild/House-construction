"""Chariot de rangement à toit ouvert, sur roulettes, glissé sous un plan de
granit porté par 2 pieds (le "trou" sous le plan de travail).

Contraintes mesurées par l'utilisateur (espace disponible) :
    hauteur libre sol -> dessous granit : 280 mm
    largeur libre entre les 2 pieds     : 990 mm
    profondeur du débord de granit      : 800 mm

Convention d'axes (comme three.js) : Y = hauteur, X/Z = plan horizontal.
Origine : centre en X, sol en Y=0, profondeur de 0 (arrière, sous le granit)
à D (avant, côté poignée).
"""

from atelier import Furniture, Hardware, Material, Panel

# --- Espace disponible (mesuré) --------------------------------------------

HAUTEUR_LIBRE = 280.0
LARGEUR_LIBRE = 990.0
PROFONDEUR_LIBRE = 800.0

# --- Hypothèses matérielles à vérifier avant découpe ------------------------

# ⚠️ Hauteur totale d'une roulette pivotante Ø40mm à platine (roue + platine
# de fixation), valeur courante du marché. C'est le paramètre le plus
# sensible du projet : à confirmer avec la fiche technique du modèle acheté
# avant de couper quoi que ce soit. Si la roulette réelle est plus haute,
# réduire HAUTEUR_COTE d'autant.
HAUTEUR_ROULETTE_MM = 55.0

MARGE_HAUTEUR_MM = 10.0  # jeu pour irrégularité du sol / du dessous du granit
MARGE_LARGEUR_MM = 30.0  # jeu total (2 x 15mm) pour le passage entre les pieds
MARGE_PROFONDEUR_MM = 20.0  # jeu total pour l'insertion + accès à la poignée

MELAMINE = Material(name="Mélaminé 16mm", thickness_mm=16.0, price_per_m2=18.0, color="#e5e0d5")

# --- Dimensions du coffre, dérivées de l'espace disponible -------------------

LARGEUR = LARGEUR_LIBRE - MARGE_LARGEUR_MM          # 960 mm (extérieur)
PROFONDEUR = PROFONDEUR_LIBRE - MARGE_PROFONDEUR_MM  # 780 mm (extérieur)
HAUTEUR_COTE = (
    HAUTEUR_LIBRE - MARGE_HAUTEUR_MM - HAUTEUR_ROULETTE_MM - MELAMINE.thickness_mm
)  # hauteur des côtés/face avant/face arrière/cloison, ~195 mm

T = MELAMINE.thickness_mm


def build() -> Furniture:
    f = Furniture(
        name="Chariot de rangement sous granit",
        description=(
            f"Coffre à toit ouvert sur 4 roulettes pivotantes Ø40mm, glissé sous un plan de "
            f"granit ({LARGEUR_LIBRE:.0f}x{HAUTEUR_LIBRE:.0f}x{PROFONDEUR_LIBRE:.0f}mm de jeu), "
            f"tiré par une poignée en façade. Cloison centrale : 2 compartiments pour bacs de tri. "
            f"⚠️ Hauteur roulette supposée à {HAUTEUR_ROULETTE_MM:.0f}mm — à vérifier avant découpe."
        ),
    )

    y_bas_cote = HAUTEUR_ROULETTE_MM + T          # haut du fond = bas des côtés
    y_centre_cote = y_bas_cote + HAUTEUR_COTE / 2   # centre vertical des panneaux verticaux

    # Fond : posé sur les roulettes.
    f.add_panel(
        Panel(
            name="Fond",
            length_mm=LARGEUR,
            width_mm=PROFONDEUR,
            material=MELAMINE,
            position_mm=(0.0, HAUTEUR_ROULETTE_MM + T / 2, PROFONDEUR / 2),
            rotation_deg=(90, 0, 0),
        )
    )

    # Côtés gauche/droit.
    x_cote = LARGEUR / 2 - T / 2
    for nom, signe in (("Côté gauche", -1), ("Côté droit", 1)):
        f.add_panel(
            Panel(
                name=nom,
                length_mm=HAUTEUR_COTE,
                width_mm=PROFONDEUR,
                material=MELAMINE,
                position_mm=(signe * x_cote, y_centre_cote, PROFONDEUR / 2),
                rotation_deg=(90, 0, 90),
            )
        )

    # Face arrière (côté fond du renfoncement) et face avant (côté poignée),
    # encastrées entre les deux côtés.
    largeur_interieure = LARGEUR - 2 * T
    f.add_panel(
        Panel(
            name="Face arrière",
            length_mm=largeur_interieure,
            width_mm=HAUTEUR_COTE,
            material=MELAMINE,
            position_mm=(0.0, y_centre_cote, T / 2),
            rotation_deg=(0, 0, 0),
        )
    )
    f.add_panel(
        Panel(
            name="Face avant",
            length_mm=largeur_interieure,
            width_mm=HAUTEUR_COTE,
            material=MELAMINE,
            position_mm=(0.0, y_centre_cote, PROFONDEUR - T / 2),
            rotation_deg=(0, 0, 0),
            note="Perçage centré pour la poignée métallique.",
        )
    )

    # Cloison centrale : sépare le coffre en 2 compartiments (bacs de tri).
    f.add_panel(
        Panel(
            name="Cloison centrale",
            length_mm=HAUTEUR_COTE,
            width_mm=PROFONDEUR - 2 * T,
            material=MELAMINE,
            position_mm=(0.0, y_centre_cote, PROFONDEUR / 2),
            rotation_deg=(90, 0, 90),
            note="Sépare les 2 bacs de tri.",
        )
    )

    f.add_hardware(Hardware(name="Roulette pivotante Ø40mm", qty=4, unit_price=4.5, note="Vérifier hauteur totale avant découpe"))
    f.add_hardware(Hardware(name="Vis de fixation roulette", qty=16, unit_price=0.05))
    f.add_hardware(Hardware(name="Poignée métallique", qty=1, unit_price=8.0, note="Fixée en façade, centrée"))
    f.add_hardware(Hardware(name="Vis à bois/mélaminé 4x30mm", qty=40, unit_price=0.04, note="Assemblage des panneaux"))

    return f
