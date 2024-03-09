import datetime
import logging
from typing import Optional, List

import requests
from bs4 import BeautifulSoup

from stockrec.extract import extract_forecast, extract_forecasts

isoweekday_to_weekday = {1: 'mandagens',
                         2: 'tisdagens',
                         3: 'onsdagens',
                         4: 'torsdagens',
                         5: 'fredagens',
                         6: 'lordagens',
                         7: 'sondagens'}


def weekday_str(date: datetime.date) -> str:
    return isoweekday_to_weekday[date.isoweekday()]


def retrieve_html(date: datetime.date, url=None) -> str:
    # TODO: Refactor to handle many urls
    if url is None:
        url = f"https://www.avanza.se/placera/redaktionellt/{date.strftime('%Y/%m/%d')}/{weekday_str(date)}-alla-nya-aktierekar.html"
    logging.debug(f"Fetching forecast information from: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        logging.info(f"Using forecast information from: {url}")
        return response.text
    url = f"https://www.avanza.se/placera/redaktionellt/{date.strftime('%Y/%m/%d')}/har-ar-{weekday_str(date)}-alla-aktierekar.html"
    logging.debug(f"Fetching forecast information from: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        logging.info(f"Using forecast information from: {url}")
        return response.text
    url = f"https://www.avanza.se/placera/redaktionellt/{date.strftime('%Y/%m/%d')}/{weekday_str(date)}-nya-aktierekar.html"
    logging.debug(f"Fetching forecast information from: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        logging.info(f"Using forecast information from: {url}")
        return response.text
    return None


def get_statements(html: str) -> List:
    soup = BeautifulSoup(html, 'html.parser')
    potential_rec = [p.get_text() for p in soup.find_all('div', 'rich-text text parbase section')[0].find_all('p')]

    for p in potential_rec:
        statement = p.strip()
        if len(statement) == 0:
            continue
        yield statement


def get_forecasts(date=datetime.date.today(), url=None):
    logging.info(f"Handle forecasts for {date}.")
    html = retrieve_html(date, url)
    if html is not None:
        return extract_forecasts(get_statements(html), date)
    else:
        logging.warning(f"Forecast page not found for {date}.")
        return []

