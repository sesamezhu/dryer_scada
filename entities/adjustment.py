import time
import typing
from dataclasses import dataclass, asdict, fields, replace, field


@dataclass
class Adjustment:
    instrument_id: int = 0
    pressure: float = 0.0
    begin: float = time.time()
    end: float = 0.0
    effect: bool = False
    success: bool = False
