"""Modélisation des assemblages entre panneaux d'un meuble.

Un `Joint` décrit comment deux panneaux sont fixés l'un à l'autre. À partir
de son type et de sa longueur, la quincaillerie nécessaire est calculée
automatiquement (au lieu d'être devinée à la main), et une notice de
montage ordonnée peut être générée.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

from .hardware import Hardware
from .hardware_catalog import recommended_screw

# Espacement usuel entre fixations le long d'un joint, en mm.
_SPACING_MM = {
    "vis_directe": 150.0,
    "tourillons": 100.0,
    "excentriques": 180.0,
    "clous": 120.0,
}

GLUE_HARDWARE_NAME = "Colle à bois (pot)"
_GLUE_MARKER_COUNT_FALLBACK = 3  # pour les joints collés sans fixation comptable (queue d'aronde)


class JointType(Enum):
    VIS_EQUERRE = "vis_equerre"      # équerre + vis, ponctuel (ex: tablette sur un côté)
    VIS_DIRECTE = "vis_directe"      # vis directes réparties le long du joint
    TOURILLONS = "tourillons"        # tourillons collés, répartis le long du joint
    EXCENTRIQUES = "excentriques"    # vérins/excentriques (meuble en kit), répartis
    CLOUS = "clous"                  # pointes réparties (ex: fond cloué)
    QUEUE_ARONDE = "queue_aronde"    # assemblage bois-bois, pas de quincaillerie


JOINT_LABELS = {
    JointType.VIS_EQUERRE: "vissé avec équerre",
    JointType.VIS_DIRECTE: "vissé directement",
    JointType.TOURILLONS: "chevillé (tourillons collés)",
    JointType.EXCENTRIQUES: "assemblé par vérins/excentriques",
    JointType.CLOUS: "cloué",
    JointType.QUEUE_ARONDE: "assemblé à queue d'aronde",
}


def _fastener_count(length_mm: float, joint_type: JointType) -> int:
    spacing = _SPACING_MM[joint_type.value]
    return max(2, round(length_mm / spacing) + 1)


@dataclass
class Joint:
    """Un assemblage entre deux panneaux, nommés par leur `Panel.name`.

    Convention : `panel_a` est le panneau **traversé** par la fixation (là
    où on verrait la tête de vis/le clou une fois monté), `panel_b` celui
    dans lequel elle est plantée. Cet ordre sert à positionner les
    marqueurs 3D de la quincaillerie (voir `atelier/contact.py`) — pour un
    assemblage symétrique (ex. `QUEUE_ARONDE`) ou une équerre (vis dans les
    deux panneaux), l'ordre a moins d'importance mais reste utilisé comme
    convention par défaut.
    """

    panel_a: str
    panel_b: str
    type: JointType
    length_mm: float
    note: str = ""

    def hardware(self, thickness_mm: float) -> list[Hardware]:
        if self.type is JointType.VIS_EQUERRE:
            return [
                Hardware(name="Équerre de fixation", qty=1, unit_price=0.6),
                Hardware(name=recommended_screw(thickness_mm), qty=4, unit_price=0.05),
            ]
        if self.type is JointType.VIS_DIRECTE:
            count = _fastener_count(self.length_mm, self.type)
            return [Hardware(name=recommended_screw(thickness_mm), qty=count, unit_price=0.05)]
        if self.type is JointType.CLOUS:
            count = _fastener_count(self.length_mm, self.type)
            return [Hardware(name="Pointe 15mm", qty=count, unit_price=0.02)]
        if self.type is JointType.TOURILLONS:
            count = _fastener_count(self.length_mm, self.type)
            return [Hardware(name="Tourillon Ø8x30mm", qty=count, unit_price=0.05)]
        if self.type is JointType.EXCENTRIQUES:
            count = _fastener_count(self.length_mm, self.type)
            return [Hardware(name="Kit vérin + tourillon", qty=count, unit_price=0.35)]
        if self.type is JointType.QUEUE_ARONDE:
            return []
        raise ValueError(f"Type de joint non géré : {self.type}")

    def uses_glue(self) -> bool:
        return self.type in (JointType.TOURILLONS, JointType.QUEUE_ARONDE)

    def hardware_with_glue(self, thickness_mm: float) -> list[Hardware]:
        """Comme `hardware()`, mais avec une ligne de colle synthétique en plus
        si le joint est collé. Le `qty` de cette ligne de colle ne représente
        PAS un vrai nombre de pots (voir `aggregate_hardware`, qui n'en compte
        qu'un seul au total) : il sert uniquement à savoir combien de points de
        colle approximatifs afficher en 3D pour ce joint.
        """
        lines = list(self.hardware(thickness_mm))
        if self.uses_glue():
            glue_qty = (
                _fastener_count(self.length_mm, JointType.TOURILLONS)
                if self.type is JointType.TOURILLONS
                else _GLUE_MARKER_COUNT_FALLBACK
            )
            lines.append(Hardware(name=GLUE_HARDWARE_NAME, qty=glue_qty, unit_price=0.0))
        return lines


def aggregate_hardware(joints: list[Joint], thickness_by_panel: dict[str, float]) -> list[Hardware]:
    """Quincaillerie totale de tous les joints (fusionne les lignes identiques)."""
    counts: dict[tuple[str, float], int] = defaultdict(int)
    needs_glue = False
    for joint in joints:
        thickness = min(
            thickness_by_panel.get(joint.panel_a, 18.0),
            thickness_by_panel.get(joint.panel_b, 18.0),
        )
        for hw in joint.hardware(thickness):
            counts[(hw.name, hw.unit_price)] += hw.qty
        if joint.uses_glue():
            needs_glue = True

    hardware = [Hardware(name=name, qty=qty, unit_price=price) for (name, price), qty in sorted(counts.items())]
    if needs_glue:
        hardware.append(Hardware(name=GLUE_HARDWARE_NAME, qty=1, unit_price=6.0))
    return hardware


def render_assembly_steps(joints: list[Joint]) -> list[str]:
    """Notice de montage ordonnée, une étape par joint (dans l'ordre d'ajout)."""
    steps = []
    for i, joint in enumerate(joints, start=1):
        label = JOINT_LABELS[joint.type]
        extra = f" — {joint.note}" if joint.note else ""
        steps.append(f"{i}. Assembler **{joint.panel_a}** et **{joint.panel_b}** ({label}){extra}.")
    return steps
