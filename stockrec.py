import datetime
import logging

import fire

from stockrec.extract import extract_forecasts, extract_forecast
from stockrec.fetch import get_forecasts
from stockrec.pgstore import ForecastStorage


class Stockrec(object):
    """Scrape new stock forecasts."""

    def __init__(self, log_level='INFO'):
        logging.basicConfig(level=log_level)

    def today(self):
        """Scrape forecasts from today."""
        storage_con = ForecastStorage()
        for f in get_forecasts(datetime.date.today()):
            storage_con.store(f)

    def range(self, start, stop=datetime.date.today().isoformat()):
        """Scrape forecasts from start date to stop date."""
        start_date = datetime.date.fromisoformat(start)
        stop_date = datetime.date.fromisoformat(stop)
        storage_con = ForecastStorage()
        day_count = (stop_date - start_date).days + 1
        for date in [start_date + datetime.timedelta(n) for n in range(day_count)]:
            logging.debug(f"Processing {date}.")
            for f in get_forecasts(date):
                storage_con.store(f)

    def refresh(self):
        """Refresh values in database based on earlier refreshed strings. Useful after a recent update of stockrec."""
        storage_con = ForecastStorage()
        no_processed = 0
        no_failed = 0
        no_refreshed = 0
        for f in storage_con.fetch_stored_raw():
            no_processed += 1
            new_f = extract_forecast(f.raw, f.date)
            if new_f.extractor is None:
                no_failed += 1
                logging.warning(f"Could not extract: {f.raw}")
            elif new_f != f:
                no_refreshed += 1
                storage_con.store(new_f)
        percent_failed = int(100*float(no_failed)/float(no_processed))
        percent_refreshed = int(100*float(no_refreshed)/float(no_processed))
        logging.info(f"Of total {no_processed} forecasts, {no_failed}({percent_failed}%) could not be parsed.")
        logging.info(f"Of total {no_processed} forecasts, {no_refreshed}({percent_refreshed}%) was updated.")


if __name__ == '__main__':
    fire.Fire(Stockrec)
