FROM python:3.12-alpine

COPY stockrec /app/stockrec/
COPY tests /app/tests/
WORKDIR /app
COPY stockrec.py setup.py README.md /app/

RUN python setup.py install