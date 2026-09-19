"""Petites règles pratiques pour choisir de la quincaillerie standard,
à défaut d'un choix explicite de l'utilisateur.
"""


def recommended_screw(thickness_mm: float) -> str:
    """Vis à bois recommandée pour fixer/traverser un panneau de cette épaisseur."""
    if thickness_mm <= 12:
        diameter = 3.5
    elif thickness_mm <= 22:
        diameter = 4.0
    else:
        diameter = 5.0
    length = round(thickness_mm * 2 + 10)
    return f"Vis à bois {diameter:g}x{length}mm"
