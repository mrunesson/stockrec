# Stockrec

Web scraper of stock forecasts that stores the data for further analysis in Postgresql.
The scraper is idempotent which means you can scrape the same day several times without
get duplicates but new recommendations are added. If same day is scraped with a new version
of the scraper it will apply existing improvements from scraper on the data.

## Build

Build dockerfile for X86 and ARM:
`docker buildx build --push -t magru/stockrec:latest --platform=linux/amd64,linux/arm64,linux/arm/v7 .`
