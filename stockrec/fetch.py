import datetime
import logging
from typing import Optional, List

import requests
from bs4 import BeautifulSoup

from stockrec.extract import extract_forecast

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
    return f"https://www.avanza.se/placera/redaktionellt/{date.strftime('%Y/%m/%d')}/{weekday_str(date)}-alla-nya-aktierekar.html"


def retrieve_html(date: datetime.date) -> str:
    url = create_url(date)
    logging.debug(f"Fetching forecast information from: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None


def parse_page(html: str) -> List:
    soup = BeautifulSoup(html, 'html.parser')
    potential_rec = [p.get_text() for p in soup.find_all('div', 'parbase rich-text section text')[0].find_all('p')]

    for p in potential_rec:
        if len(p.strip()) == 0:
            continue
        forecast = extract_forecast(p)
        yield forecast


def get_forecast(date=datetime.date.today()):
    no_processed = 0
    no_failed = 0
    logging.info(f"Handle forecasts for {date}")
    html = retrieve_html(date)
    if html is not None:
        for forecast in parse_page(html):
            no_processed += 1
            if forecast.extractor is None:
                no_failed += 1
                logging.warning(f"Could not extract: {forecast.raw}")
            yield forecast
        percent = int(100*float(no_failed)/float(no_processed))
        logging.info(f"Of total {no_processed} forecasts, {no_failed}({percent}%) could not be parsed for {date}.")
    else:
        logging.warning(f"Forecast page not found for {date}.")

