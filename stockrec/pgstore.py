import logging
import ssl
from ssl import SSLContext

import pg8000

from stockrec.model import Forecast, Signal, Direction
import os


class ForecastStorage:

    _schema = [
        f"""CREATE TYPE signal AS ENUM ({", ".join(["'"+n.name+"'" for n in list(Signal)])})""",
        f"""CREATE TYPE direction AS ENUM ({", ".join(["'"+n.name+"'" for n in list(Direction)])})""",
        f"""CREATE OR REPLACE FUNCTION set_update_time()   
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.last_updated = now();
                RETURN NEW;   
            END;
            $$ language 'plpgsql'""",
        """CREATE TABLE IF NOT EXISTS forecasts (
           date                 DATE NOT NULL,
           analyst              TEXT NULL,
           company              TEXT NULL,
           direction            direction NOT NULL DEFAULT 'UNKNOWN',
           signal               signal NOT NULL DEFAULT 'UNKNOWN',
           forecast_price       NUMERIC(12,4) CHECK (forecast_price >=0 OR forecast_price IS NULL),
           prev_signal          signal NOT NULL DEFAULT 'UNKNOWN',
           prev_forecast_price  NUMERIC(12,4) CHECK (prev_forecast_price >=0 OR prev_forecast_price IS NULL),
           currency             VARCHAR(10) NULL,
           raw                  TEXT NOT NULL CHECK (raw <> ''),
           extractor            VARCHAR(20) CHECK (extractor <> '' OR extractor IS NULL),
           md5                  VARCHAR(32) NOT NULL CHECK (length(md5) = 32) PRIMARY KEY,
           locked               BOOLEAN NOT NULL DEFAULT FALSE,
           last_updated         TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
           )""",
        """CREATE TRIGGER set_update_time 
           BEFORE UPDATE ON forecasts FOR EACH ROW 
           EXECUTE PROCEDURE set_update_time()"""
    ]

    def __init__(self):
        user = os.getenv("PG_USER", 'postgres')
        password = os.getenv("PG_PASSWORD", None)
        self._database = os.getenv("PG_DATABASE", 'postgres')
        host = os.getenv("PG_HOST", 'localhost')
        port = int(os.getenv("PG_PORT", '5432'))
        ssl_context = SSLContext()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        self._con = pg8000.connect(user, host, self._database, port, password)
        self._con.autocommit = True
        self._create_schema()

    def _has_forecast_table(self) -> bool:
        return len(
            self._con.run(
                "SELECT * FROM information_schema.tables WHERE table_name='forecasts'"
            )
        ) == 1

    def _create_schema(self):
        if not self._has_forecast_table():
            for s in self._schema:
                self._con.run(s)

    def store(self, forecast: Forecast):
        self._con.run("""
            INSERT INTO forecasts (
              date,
              analyst,
              company,
              direction,
              signal, 
              forecast_price, 
              prev_signal, 
              prev_forecast_price, 
              currency, 
              raw, 
              extractor, 
              md5) 
            VALUES (
              :date,
              :analyst,
              :company,
              :direction,
              :signal, 
              :forecast_price, 
              :prev_signal, 
              :prev_forecast_price, 
              :currency, 
              :raw, 
              :extractor, 
              md5(:raw)
            )
            ON CONFLICT (md5) WHERE locked IS FALSE DO UPDATE SET
              (date, 
              analyst, 
              company, 
              direction, 
              signal, 
              forecast_price, 
              prev_signal, 
              prev_forecast_price, 
              currency, 
              extractor) = ROW (
              :date,
              :analyst,
              :company,
              :direction,
              :signal,
              :forecast_price,
              :prev_signal,
              :prev_forecast_price,
              :currency,
              :extractor)""",
                        date=forecast.date,
                        analyst=forecast.analyst,
                        company=forecast.company,
                        direction=forecast.change_direction.name,
                        signal=forecast.signal.name,
                        forecast_price=forecast.forecast_price,
                        prev_signal=forecast.prev_signal.name,
                        prev_forecast_price=forecast.prev_forecast_price,
                        currency=forecast.currency,
                        raw=forecast.raw,
                        extractor=forecast.extractor
                        )

    def fetch_stored_raw(self):
        records = self._con.run(
            """SELECT date,
                      analyst,
                      company,
                      direction,
                      signal,
                      forecast_price,
                      prev_signal,
                      prev_forecast_price,
                      currency,
                      extractor,
                      raw
                FROM forecasts""")
        return [Forecast(date=r[0],
                         analyst=r[1],
                         company=r[2],
                         change_direction=Direction[r[3]],
                         signal=Signal[r[4]],
                         forecast_price=r[5],
                         prev_signal=Signal[r[6]],
                         prev_forecast_price=r[7],
                         currency=r[8],
                         extractor=r[9],
                         raw=r[10]) for r in records]
