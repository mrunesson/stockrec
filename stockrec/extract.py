import datetime
import decimal
import logging
import re

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
    'pund': 'GDP',
    'schweizerfranc': 'CHF',
}


def to_float(value: str):
    if value is not None:
        try:
            return decimal.Decimal(value.replace(',', '.').replace(':', '.'))
        except decimal.InvalidOperation:
            return None
    else:
        return None


def idx_in_list(l: List[str], values: List[str]) -> List[int]:
    return [idx for idx, t in enumerate(l) if t in values]


def single_idx_in_list(l: List[str], values: List[str]) -> int:
    idx = idx_in_list(l, values)
    if len(idx) == 0:
        return -1
    elif len(idx) > 1:
        return -2
    return idx[0]


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
    cleaned_text = re.sub("\.([A-Z])", " \\1", text)
    tokens = [s.strip(u',.\xa0') for s in cleaned_text.split(' ') if s != '']
    tokens = [t for t in tokens if t not in ['*']]
    tokens = merge_number_tokens(tokens)
    tokens = merge_parenthesis_tokens(tokens)
    tokens = merge_terms_in_tokens(tokens)
    return tokens


def extract_simple(text: str, date: datetime.date):
    # Kepler Cheuvreux sänker LVMH till behåll (köp), riktkurs 400 euro.
    # Bank of America Merrill Lynch sänker EQT till underperform (neutral)
    if 'riktkursen för' in text:
        return None
    tokens = tokenize(text)
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
                              raw=text,
                              date=date,
                              analyst=' '.join(tokens[:direction_idx[0]]),
                              change_direction=Direction.from_text(tokens[direction_idx[0]]),
                              company=' '.join(tokens[direction_idx[0]+1:till_idx[0]]),
                              signal=Signal.from_text(tokens[signal_idx[0]]),
                              prev_signal=prev_signal,
                              forecast_price=forecast_price,
                              prev_forecast_price=prev_forecast_price,
                              currency=currency)
    return forecast


def extract_bn(in_str: str, date: datetime.date):
    # Morgan Stanley sänker riktkursen för Lundin Energy till 245 kronor (325), upprepar jämvikt - BN
    # Deutsche Bank höjer riktkursen för Boliden till 250 kronor från 235 kronor. Rekommendationen köp upprepas. Det framgår av ett marknadsbrev.
    # Pareto Securities höjer riktkursen för investmentbolaget Kinnevik till 290 kronor från 262 kronor, enligt en ny analys.
    tokens = tokenize(in_str)
    direction_idx = idx_in_list(tokens, text_to_direction.keys())
    for_idx = idx_in_list(tokens, ['för'])
    till_idx = idx_in_list(tokens, ['till'])
    fran_idx = idx_in_list(tokens, ['från'])
    signal_idx = idx_in_list(tokens, text_to_signal.keys())

    if len(direction_idx) == 0 or len(till_idx) == 0 or len(for_idx) == 0:
        return None
    if direction_idx[0] > for_idx[0] or for_idx[0] > till_idx[0]:
        return None

    signal = Signal.UNKNOWN
    prev_signal = Signal.UNKNOWN
    if len(signal_idx) > 0:
        signal = Signal.from_text(tokens[signal_idx[0]])
        if 'upprepar' in tokens or 'upprepas' in tokens:
            prev_signal = signal
        else:
            prev_signal_candidate = tokens[signal_idx[0] + 1]
            if is_parentheses_enclosed(prev_signal_candidate):
                prev_signal = Signal.from_text(prev_signal_candidate[1:-1])

    forecast_price = to_float(tokens[till_idx[0]+1])
    currency = None
    prev_forecast_price = None
    if forecast_price is not None:
        currency= currencies[tokens[till_idx[0]+2]]
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
                              date=date,
                              analyst=' '.join(tokens[:direction_idx[0]]),
                              change_direction=Direction.from_text(tokens[direction_idx[0]]),
                              company=' '.join(tokens[for_idx[0]+1:till_idx[0]]),
                              signal=signal,
                              prev_signal=prev_signal,
                              forecast_price=forecast_price,
                              prev_forecast_price=prev_forecast_price,
                              currency=currency)
    return forecast


def extract_no_analyst(text: str, date: datetime.date):
    # Castellum höjs sitt behåll (sälj), med riktkurs 165 kronor (200)
    tokens = tokenize(text)
    direction_idx = single_idx_in_list(tokens, text_to_direction.keys())
    sitt_idx = single_idx_in_list(tokens, ['sitt'])
    riktkurs_idx = single_idx_in_list(tokens, ['riktkurs'])

    if not(direction_idx < sitt_idx < riktkurs_idx):
        return None

    signal=Signal.from_text(tokens[sitt_idx+1])
    prev_signal_candidate = tokens[sitt_idx+2]
    if is_parentheses_enclosed(prev_signal_candidate):
        prev_signal = Signal.from_text(prev_signal_candidate[1:-1])
    else:
        prev_signal = Signal.UNKNOWN

    forecast_price = to_float(tokens[riktkurs_idx+1])
    prev_forecast_price = None
    if len(tokens) > riktkurs_idx+3:
        prev_forecast_price = to_float(tokens[riktkurs_idx+3][1:-1])

    forecast = model.Forecast(extractor='no_analyst',
                              raw=text,
                              date=date,
                              analyst=None,
                              change_direction=Direction.from_text(tokens[direction_idx]),
                              company=' '.join(tokens[0:direction_idx]),
                              signal=signal,
                              prev_signal=prev_signal,
                              forecast_price=forecast_price,
                              prev_forecast_price=prev_forecast_price,
                              currency=currencies[tokens[riktkurs_idx+2]])
    return forecast


def extract_inled(text: str, date: datetime.date):
    # BTIG inleder bevakning på Tripadvisor med rekommendationen neutral.
    tokens = tokenize(text)
    inleder_idx = idx_in_list(tokens, ['inleder'])
    med_idx = idx_in_list(tokens, ['med'])

    if len(inleder_idx) != 1 or len(med_idx) != 1:
        return None
    if inleder_idx[0] > med_idx[0]:
        return None

    forecast = model.Forecast(extractor='inled',
                              raw=text,
                              date=date,
                              analyst=' '.join(tokens[:inleder_idx[0]]),
                              change_direction=Direction.NEW,
                              company=' '.join(tokens[inleder_idx[0]+3:med_idx[0]]),
                              signal=Signal.from_text(tokens[med_idx[0]+2]),
                              prev_signal=Signal.UNKNOWN,
                              forecast_price=None,
                              prev_forecast_price=None,
                              currency=None)
    return forecast


def extract_bloomberg(text: str, date: datetime.date):
    # "Goldman Sachs & Co sänker sin rekommendation för Outokumpu till neutral från köp."
    tokens = tokenize(text)
    sin_idx = single_idx_in_list(tokens, ['sin'])
    for_idx = single_idx_in_list(tokens, ['för'])
    till_idx = single_idx_in_list(tokens, ['till'])
    fran_idx = single_idx_in_list(tokens, ['från'])

    if not (0 < sin_idx < for_idx < till_idx < fran_idx):
        return None

    forecast = model.Forecast(extractor='bloomberg',
                              raw=text,
                              date=date,
                              analyst=' '.join(tokens[:sin_idx-1]),
                              change_direction=Direction.from_text(tokens[sin_idx-1]),
                              company=' '.join(tokens[for_idx+1:till_idx]),
                              signal=Signal.from_text(tokens[till_idx+1]),
                              prev_signal=Signal.from_text(tokens[fran_idx+1]),
                              forecast_price=None,
                              prev_forecast_price=None,
                              currency=None)
    return forecast


def extract_motivated_value(text: str, date: datetime.date):
    # "Redeye höjer motiverat värde för Systemair till 168 kronor (155)."
    # Redeye höjer sitt motiverade värde i basscenariot för bettingbolaget Enlabs till 30 kronor, från tidigare 29 kronor.
    # Might not be needed anymore after extract_bn generalised.
    tokens = tokenize(text)
    motiverat_idx = single_idx_in_list(tokens, ['motiverat'])
    varde_idx = single_idx_in_list(tokens, ['värde'])
    for_idx = single_idx_in_list(tokens, ['för',])
    till_idx = single_idx_in_list(tokens, ['till'])

    if motiverat_idx+1 != varde_idx:
        return None
    if for_idx > till_idx:
        return None

    prev_forecast_price = None
    if len(tokens)-1 >= till_idx+3 and is_parentheses_enclosed(tokens[till_idx+3]):
        prev_forecast_price = to_float(tokens[till_idx+3][1:-1])
    currency=currencies[tokens[till_idx+2]]

    forecast = model.Forecast(extractor='motivated_value',
                              raw=text,
                              date=date,
                              analyst=' '.join(tokens[:motiverat_idx-1]),
                              change_direction=Direction.from_text(tokens[motiverat_idx-1]),
                              company=' '.join(tokens[for_idx+1:till_idx]),
                              signal=Signal.UNKNOWN,
                              prev_signal=Signal.UNKNOWN,
                              forecast_price=to_float(tokens[till_idx+1]),
                              prev_forecast_price=prev_forecast_price,
                              currency=currency)
    return forecast


def extract_forecast(text: str, date: datetime.date):
    logging.debug(f"Extracting: {text}")
    result = extract_simple(text, date)
    if result is not None:
        return result
    result = extract_bloomberg(text, date)
    if result is not None:
        return result
    result = extract_bn(text, date)
    if result is not None:
        return result
    result = extract_no_analyst(text, date)
    if result is not None:
        return result
    result = extract_inled(text, date)
    if result is not None:
        return result
    result = extract_motivated_value(text, date)
    if result is not None:
        return result
    return model.Forecast(raw=text, date=date)


def extract_forecasts(statements, date: datetime.date):
    no_processed = 0
    no_failed = 0
    for statement in statements:
        forecast = extract_forecast(statement, date)
        no_processed += 1
        if forecast.extractor is None:
            no_failed += 1
            logging.warning(f"Could not extract: {forecast.raw}")
        yield forecast
    percent = int(100*float(no_failed)/float(no_processed))
    logging.info(f"Of total {no_processed} forecasts, {no_failed}({percent}%) could not be parsed.")
