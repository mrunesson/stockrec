import datetime
import logging
from typing import Optional, List

import requests
from bs4 import BeautifulSoup

from stockrec.extract import extract_forecast
from stockrec.pgstore import ForecastStorage

isoweekday_to_weekday = {1: 'måndagens',
                         2: 'tisdagens',
                         3: 'onsdagens',
                         4: 'torsdagens',
                         5: 'fredagens',
                         6: 'lördagens',
                         7: 'söndagens'}


def weekday_str(date: datetime.date) -> str:
    return isoweekday_to_weekday[date.isoweekday()]


def create_url(date: datetime.date) -> Optional[str]:
    if date.isoweekday() >= 6:
        return None
    return f"https://www.avanza.se/placera/redaktionellt/{date.strftime('%Y/%m/%d')}/{weekday_str(date)}-alla-nya-aktierekar.html"


def retrieve_html(date: datetime.date) -> str:
    url = create_url(date)
    logging.info(f"Fetching forecasts from: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None


def read_file(file: str) -> str:
    with open(file) as f:
        content=f.read()
    return content


def parse_page(html: str) -> List:
    soup = BeautifulSoup(html, 'html.parser')
    potential_rec = [p.get_text() for p in soup.find_all('div', 'parbase rich-text section text')[0].find_all('p')]

    no_processed = 0
    no_failed = 0
    for p in potential_rec:
        if len(p.strip()) == 0:
            continue
        no_processed += 1
        logging.debug(f"Processing: {p}")
        forecast = extract_forecast(p)
        if forecast.extractor is None:
            no_failed += 1
            logging.warning(f"Could not extract: {p}")
        yield forecast
    logging.info(f"Of total {no_processed} forecasts, {no_failed}({int(100*float(no_failed)/float(no_processed))}%) could not be parsed.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    storage_con=ForecastStorage()
    #parse_page(read_file('onsdagens-alla-nya-aktierekar.html'))
    html = retrieve_html(datetime.date.today())
    if html is not None:
        for forecast in parse_page(html):
            storage_con.store(forecast)
    else:
        logging.warning("Forecast page not found.")

