import datetime
import logging
from typing import Optional, List

import requests
from bs4 import BeautifulSoup

from stockrec.extract import extract_forecast, extract_forecasts

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


def get_statements(html: str) -> List:
    soup = BeautifulSoup(html, 'html.parser')
    potential_rec = [p.get_text() for p in soup.find_all('div', 'parbase rich-text section text')[0].find_all('p')]

    for p in potential_rec:
        statement = p.strip()
        if len(statement) == 0:
            continue
        yield statement


def get_forecasts(date=datetime.date.today()):
    logging.info(f"Handle forecasts for {date}.")
    html = retrieve_html(date)
    if html is not None:
        return extract_forecasts(get_statements(html), date)
    else:
        logging.warning(f"Forecast page not found for {date}.")
        return []

