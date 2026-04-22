from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: int
    username: str
    display_name: str
    balance: int
    role: str


@dataclass
class Stock:
    id: int
    name: str
    symbol: str
    current_price: int
    change_rate: Optional[float] = None
