import datetime
from typing import Optional, NamedTuple
from enum import Enum, unique

@unique
class Signal(Enum):
    UNKNOWN = 0
    SELL = 1
    UNDERPERFORM = 2
    NEUTRAL = 3
    HOLD = 4
    OUTPERFORM = 5
    BUY = 6

    @classmethod
    def from_text(cls, value: str) -> Enum:
        return text_to_signal.get(value, Signal.UNKNOWN)


text_to_signal = {
    'sälj': Signal.SELL,
    'minska': Signal.SELL,
    'neutral': Signal.NEUTRAL,
    'jämvikt': Signal.HOLD,
    'behåll': Signal.HOLD,
    'köp': Signal.BUY,
    'öka': Signal.BUY,
    'underperform': Signal.UNDERPERFORM,
    'outperform': Signal.OUTPERFORM,
    'market perform': Signal.HOLD,
    'sector perform': Signal.HOLD,
    'övervikt': Signal.BUY,
    'undervikt': Signal.SELL,
}

@unique
class Direction(Enum):
    UNKNOWN = 0
    LOWER = 1
    NEW = 2
    UNCHANGED = 3
    RAISE = 4

    @classmethod
    def from_text(cls, value: str) -> Enum:
        return text_to_direction.get(value, Direction.UNKNOWN)


text_to_direction = {
    'sänker': Direction.LOWER,
    'höjer': Direction.RAISE,
}


class Forecast(NamedTuple):
    raw: str
    extractor: Optional[str] = None
    date: datetime.date = datetime.date.today()
    analyst: Optional[str] = None
    change_direction: Direction = Direction.UNKNOWN
    company: Optional[str] = None
    signal: Signal = Signal.UNKNOWN
    prev_signal: Signal = Signal.UNKNOWN
    forecast_price: Optional[float] = None
    prev_forecast_price: Optional[float] = None
    currency: Optional[str] = None
