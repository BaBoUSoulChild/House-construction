from dataclasses import dataclass


@dataclass
class Hardware:
    """Un élément de quincaillerie (vis, charnière, tourillon, équerre...)."""

    name: str
    qty: int
    unit_price: float = 0.0
    note: str = ""

    @property
    def total_price(self) -> float:
        return self.qty * self.unit_price
