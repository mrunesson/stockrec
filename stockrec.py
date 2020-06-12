import datetime
import logging

import fire

from stockrec.fetch import get_forecast
from stockrec.pgstore import ForecastStorage


class Stockrec(object):
    """Scrape new stock forecasts."""

    def __init__(self, log_level='INFO'):
        logging.basicConfig(level=log_level)

    def today(self):
        """Scrape forecasts from today."""
        storage_con = ForecastStorage()
        for f in get_forecast(datetime.date.today()):
            storage_con.store(f)

    def range(self, start, stop=datetime.date.today().isoformat()):
        """Scrape forecasts from start date to stop date."""
        start_date = datetime.date.fromisoformat(start)
        stop_date = datetime.date.fromisoformat(stop)
        storage_con = ForecastStorage()
        day_count = (stop_date - start_date).days + 1
        for date in [start_date + datetime.timedelta(n) for n in range(day_count)]:
            logging.debug(f"Processing {date}.")
            for f in get_forecast(date):
                storage_con.store(f)

    def refresh(self):
        """Refresh values in database based on earlier refreshed strings. Useful after a recent update of stockrec."""
        logging.critical("refresh command TBD")
        pass


if __name__ == '__main__':
    fire.Fire(Stockrec)