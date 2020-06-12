import datetime
import unittest

from stockrec.extract import extract_forecast
from stockrec.model import Forecast, Direction, Signal


class TestSimpleExtractor(unittest.TestCase):

    test_data = [
        ('Carnegie sänker Thule till behåll (köp), riktkurs 220 kronor.',
         Forecast(extractor='simple',
                  raw='Carnegie sänker Thule till behåll (köp), riktkurs 220 kronor.',
                  date=datetime.date.today(),
                  analyst='Carnegie',
                  change_direction=Direction.LOWER,
                  company='Thule',
                  signal=Signal.HOLD,
                  prev_signal=Signal.BUY,
                  forecast_price=220,
                  currency='SEK'
                  )),
        ('UBS höjer Vale till köp (neutral), riktkurs 12 dollar (13).\xa0',
         Forecast(extractor='simple',
                  raw='UBS höjer Vale till köp (neutral), riktkurs 12 dollar (13).\xa0',
                  date=datetime.date.today(),
                  analyst='UBS',
                  change_direction=Direction.RAISE,
                  company='Vale',
                  signal=Signal.BUY,
                  prev_signal=Signal.NEUTRAL,
                  forecast_price=12,
                  prev_forecast_price=13,
                  currency='USD'
                  )),
        ('Kepler Cheuvreux sänker LVMH till behåll (köp), riktkurs 400 euro.',
         Forecast(extractor='simple',
                  raw='Kepler Cheuvreux sänker LVMH till behåll (köp), riktkurs 400 euro.',
                  date=datetime.date.today(),
                  analyst='Kepler Cheuvreux',
                  change_direction=Direction.LOWER,
                  company='LVMH',
                  signal=Signal.HOLD,
                  prev_signal=Signal.BUY,
                  forecast_price=400,
                  currency='EUR'
                  )),
        ('RBC höjer Zoom till outperform (sector perform), riktkurs 250 dollar.',
         Forecast(extractor='simple',
                  raw='RBC höjer Zoom till outperform (sector perform), riktkurs 250 dollar.',
                  date=datetime.date.today(),
                  analyst='RBC',
                  change_direction=Direction.RAISE,
                  company='Zoom',
                  signal=Signal.OUTPERFORM,
                  prev_signal=Signal.HOLD,
                  forecast_price=250,
                  currency='USD'
                  )),
        ('Morgan Stanley sänker riktkursen för Lundin Energy till 245 kronor (325), upprepar jämvikt - BN',
         Forecast(extractor='bn',
                  raw='Morgan Stanley sänker riktkursen för Lundin Energy till 245 kronor (325), upprepar jämvikt - BN',
                  date=datetime.date.today(),
                  analyst='Morgan Stanley',
                  change_direction=Direction.LOWER,
                  company='Lundin Energy',
                  signal=Signal.HOLD,
                  prev_signal=Signal.HOLD,
                  forecast_price=245,
                  prev_forecast_price=325,
                  currency='SEK'
                  )),
        ('Bank of America Merrill Lynch sänker EQT till underperform (neutral)',
         Forecast(extractor='simple',
                  raw='Bank of America Merrill Lynch sänker EQT till underperform (neutral)',
                  date=datetime.date.today(),
                  analyst='Bank of America Merrill Lynch',
                  change_direction=Direction.LOWER,
                  company='EQT',
                  signal=Signal.UNDERPERFORM,
                  prev_signal=Signal.NEUTRAL,
                  forecast_price=None,
                  prev_forecast_price=None,
                  currency=None
                  )),
        ('Credit Suisse höjer riktkursen för Genmab till 2 300 danska kronor (1 950), upprepar outperform.',
         Forecast(extractor='bn',
                  raw='Credit Suisse höjer riktkursen för Genmab till 2 300 danska kronor (1 950), upprepar outperform.',
                  date=datetime.date.today(),
                  analyst='Credit Suisse',
                  change_direction=Direction.RAISE,
                  company='Genmab',
                  signal=Signal.OUTPERFORM,
                  prev_signal=Signal.OUTPERFORM,
                  forecast_price=2300,
                  prev_forecast_price=1950,
                  currency='DKK'
                  )),
        ('JP Morgan sänker D.R. Horton till neutral (övervikt), riktkurs 59 dollar (42)',
         Forecast(extractor='simple',
                  raw='JP Morgan sänker D.R. Horton till neutral (övervikt), riktkurs 59 dollar (42)',
                  date=datetime.date.today(),
                  analyst='JP Morgan',
                  change_direction=Direction.LOWER,
                  company='D.R Horton',
                  signal=Signal.NEUTRAL,
                  prev_signal=Signal.BUY,
                  forecast_price=59,
                  prev_forecast_price=42,
                  currency='USD'
                  )),
        ('Deutsche Bank höjer riktkursen för Boliden till 250 kronor från 235 kronor. Rekommendationen köp upprepas. Det framgår av ett marknadsbrev.',
         Forecast(extractor='bn',
                  raw='Deutsche Bank höjer riktkursen för Boliden till 250 kronor från 235 kronor. Rekommendationen köp upprepas. Det framgår av ett marknadsbrev.',
                  date=datetime.date.today(),
                  analyst='Deutsche Bank',
                  change_direction=Direction.RAISE,
                  company='Boliden',
                  signal=Signal.BUY,
                  prev_signal=Signal.BUY,
                  forecast_price=250,
                  prev_forecast_price=235,
                  currency='SEK'
                  )),
        ('BTIG inleder bevakning på Tripadvisor med rekommendationen neutral.',
         Forecast(extractor='inled',
                  raw='BTIG inleder bevakning på Tripadvisor med rekommendationen neutral.',
                  date=datetime.date.today(),
                  analyst='BTIG',
                  change_direction=Direction.NEW,
                  company='Tripadvisor',
                  signal=Signal.NEUTRAL,
                  prev_signal=Signal.UNKNOWN,
                  forecast_price=None,
                  prev_forecast_price=None,
                  currency=None
                  ))
    ]

    def test_extractor_simple(self):
        for s, expected in self.test_data:
            self.assertEqual(expected, extract_forecast(s))



