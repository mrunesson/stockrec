import datetime
import logging

from stockrec import model
from typing import List

from stockrec.model import Direction, Signal, text_to_signal, text_to_direction

currencies = {
    'kronor': 'SEK',
    'dollar': 'USD',
    'euro': 'EUR',
    'danska kronor': 'DKK',
    'norska kronor': 'NOK',
    'brittiska pund': 'GDP',
    'schweizerfranc': 'CHF',
}


def to_float(value: str) -> float:
    if value is not None:
        try:
            return float(value.replace(',', '.').replace(':', '.'))
        except ValueError:
            return None
    else:
        return None


def idx_in_list(l: List[str], values: List[str]) -> List[int]:
    # 'Carnegie sänker Thule till behåll (köp), riktkurs 220 kronor.'
    # 'UBS höjer Vale till köp (neutral), riktkurs 12 dollar (13).\xa0'
    return [idx for idx, t in enumerate(l) if t in values]


def is_parentheses_enclosed(value: str) -> bool:
    return value[0] == '(' and value[-1] == ')'


def merge_parenthesis_tokens(tokens: List) -> List:
    result=[]
    holder=None
    for t in tokens:
        if holder is None:
            if t[0] == '(' and t[-1] != ')':
                holder = t
            else:
                result.append(t)
        else:
            if t[-1] == ')':
                result.append(holder + ' ' + t)
                holder = None
            else:
                holder += ' ' + t
    return result


_terms = ['market perform', 'sector perform', 'norska kronor', 'danska kronor', 'brittiska pund']
_terms_start = [term.split( )[0] for term in _terms]


def merge_terms_in_tokens(tokens: List) -> List:
    result=[]
    holder=None
    for t in tokens:
        if holder is None:
            if t in _terms_start:
                holder = t
            else:
                result.append(t)
        else:
            if holder + ' ' + t in _terms:
                result.append(holder + ' ' + t)
            else:
                result.append(holder)
                result.append(t)
            holder = None
    return result


def merge_number_tokens(tokens: List) -> List:
    result=[]
    holder=None
    for t in tokens:
        if holder is None:
            if t.isnumeric() or t[1:].isnumeric():
                holder = t
            else:
                result.append(t)
        else:
            if t.isnumeric() or t[:-1].isnumeric():
                holder += t
            else:
                result.append(holder)
                result.append(t)
                holder = None
    return result


def tokenize(text: str) -> List:
    tokens = [s.strip(u',.\xa0') for s in text.split(' ') if s != '']
    tokens = merge_number_tokens(tokens)
    tokens = merge_parenthesis_tokens(tokens)
    tokens = merge_terms_in_tokens(tokens)
    return tokens


def parser_simple(in_str: str):
    # Kepler Cheuvreux sänker LVMH till behåll (köp), riktkurs 400 euro.
    # Bank of America Merrill Lynch sänker EQT till underperform (neutral)
    if 'riktkursen för' in in_str:
        return None
    tokens = tokenize(in_str)
    direction_idx = idx_in_list(tokens, text_to_direction.keys())
    till_idx = idx_in_list(tokens, ['till'])
    signal_idx = idx_in_list(tokens, text_to_signal.keys())
    forecast_idx = idx_in_list(tokens, ['riktkurs'])

    if len(direction_idx) != 1 or len(till_idx) != 1 or len(forecast_idx) > 1 or len(signal_idx) != 1:
        return None
    if direction_idx[0] > till_idx[0] or till_idx[0] > signal_idx[0]:
        return None

    prev_signal=Signal.UNKNOWN
    if signal_idx[0]+1 != len(tokens):
        prev_signal_candidate = tokens[signal_idx[0] + 1]
        if is_parentheses_enclosed(prev_signal_candidate):
            prev_signal=Signal.from_text(prev_signal_candidate[1:-1])

    forecast_price = None
    prev_forecast_price = None
    currency = None
    if len(forecast_idx) == 1:
        forecast_price = to_float(tokens[forecast_idx[0]+1])
        if forecast_price is not None:
            if tokens[forecast_idx[0]-1] == 'upprepar':
                prev_forecast_price = forecast_price
            elif len(tokens) > forecast_idx[0]+3:
                prev_forecast_price_candidate = tokens[forecast_idx[0] + 3]
                if is_parentheses_enclosed(prev_forecast_price_candidate):
                    prev_forecast_price = to_float(prev_forecast_price_candidate[1:-1])
            currency = currencies[tokens[forecast_idx[0]+2]]

    forecast = model.Forecast(extractor='simple',
                              raw=in_str,
                              date=datetime.date.today(),
                              analyst=' '.join(tokens[:direction_idx[0]]),
                              change_direction=Direction.from_text(tokens[direction_idx[0]]),
                              company=' '.join(tokens[direction_idx[0]+1:till_idx[0]]),
                              signal=Signal.from_text(tokens[signal_idx[0]]),
                              prev_signal=prev_signal,
                              forecast_price=forecast_price,
                              prev_forecast_price=prev_forecast_price,
                              currency=currency)
    return forecast


def extract_bn(in_str: str):
    # Morgan Stanley sänker riktkursen för Lundin Energy till 245 kronor (325), upprepar jämvikt - BN
    # Deutsche Bank höjer riktkursen för Boliden till 250 kronor från 235 kronor. Rekommendationen köp upprepas. Det framgår av ett marknadsbrev.
    tokens = tokenize(in_str)
    direction_idx = idx_in_list(tokens, text_to_direction.keys())
    for_idx = idx_in_list(tokens, ['för'])
    till_idx = idx_in_list(tokens, ['till'])
    fran_idx = idx_in_list(tokens, ['från'])
    signal_idx = idx_in_list(tokens, text_to_signal.keys())

    if len(direction_idx) != 1 or len(till_idx) != 1 or len(for_idx) != 1 or len(signal_idx) != 1 or len(fran_idx) > 1:
        return None
    if direction_idx[0] > for_idx[0] or for_idx[0] > till_idx[0]:
        return None

    signal=Signal.from_text(tokens[signal_idx[0]])
    if 'upprepar' in tokens or 'upprepas' in tokens:
        prev_signal = signal
    else:
        prev_signal_candidate = tokens[signal_idx[0] + 1]
        if is_parentheses_enclosed(prev_signal_candidate):
            prev_signal = prev_signal_candidate[1:-1]
        else:
            prev_signal = Signal.UNKNOWN

    forecast_price = to_float(tokens[till_idx[0]+1])
    prev_forecast_price = None
    if len(fran_idx) != 0:
        if tokens[fran_idx[0]+1].isnumeric():
            prev_forecast_price = to_float(tokens[fran_idx[0]+1])
        elif tokens[fran_idx[0]+2].isnumeric():
            prev_forecast_price = to_float(tokens[fran_idx[0]+2])
    else:
        prev_forecast_price_candidate = tokens[till_idx[0] + 3]
        if is_parentheses_enclosed(prev_forecast_price_candidate):
            prev_forecast_price = to_float(prev_forecast_price_candidate[1:-1])

    forecast = model.Forecast(extractor='bn',
                              raw=in_str,
                              date=datetime.date.today(),
                              analyst=' '.join(tokens[:direction_idx[0]]),
                              change_direction=Direction.from_text(tokens[direction_idx[0]]),
                              company=' '.join(tokens[for_idx[0]+1:till_idx[0]]),
                              signal=signal,
                              prev_signal=prev_signal,
                              forecast_price=forecast_price,
                              prev_forecast_price=prev_forecast_price,
                              currency=currencies[tokens[till_idx[0]+2]])
    return forecast


def extract_inled(in_str: str):
    # BTIG inleder bevakning på Tripadvisor med rekommendationen neutral.
    tokens = tokenize(in_str)
    inleder_idx = idx_in_list(tokens, ['inleder'])
    med_idx = idx_in_list(tokens, ['med'])

    if len(inleder_idx) != 1 or len(med_idx) != 1:
        return None
    if inleder_idx[0] > med_idx[0]:
        return None

    forecast = model.Forecast(extractor='inled',
                              raw=in_str,
                              date=datetime.date.today(),
                              analyst=' '.join(tokens[:inleder_idx[0]]),
                              change_direction=Direction.NEW,
                              company=' '.join(tokens[inleder_idx[0]+3:med_idx[0]]),
                              signal=Signal.from_text(tokens[med_idx[0]+2]),
                              prev_signal=Signal.UNKNOWN,
                              forecast_price=None,
                              prev_forecast_price=None,
                              currency=None)
    return forecast


def extract_forecast(text: str):
    logging.debug(f"Extracting: {text}")
    result = parser_simple(text)
    if result is not None:
        return result
    result = extract_bn(text)
    if result is not None:
        return result
    result = extract_inled(text)
    if result is not None:
        return result
    return model.Forecast(raw=text)
