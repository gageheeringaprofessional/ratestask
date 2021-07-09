# Setup

Execute the docker file:

```bash
docker build -t ratestask .
```

Run the container, but map your machine's port 5433 to the docker container's port 5432 since Postgres might be running on your machine:

```bash
docker run -p 0.0.0.0:5433:5432 --name ratestask ratestask
```

Connect to the Postgres database:

```bash
PGPASSWORD=ratestask psql -h 127.0.0.1 -U postgres -p 5433
```

The API was written in Python 3.

`cd` into the `api` directory and ensure you have required packages by installing the requirements specified in `setup.py`:

```bash
pip install .
```

If you have trouble installing the `psycopg2` package, please ensure you have [libpq-dev](https://stackoverflow.com/questions/20863295/how-do-i-install-psycopg2-for-python-3-x/35033570) installed on your machine.

Start the API:

```bash
python api.py
```

Run formal tests:

```bash
pytest tests.py
```

Please note that `tests.py` assumes the API is running on `127.0.0.1:5000`

You can also execute an HTTP request to test for yourself:

```bash
curl "http://127.0.0.1:5000/api/v1/average?origin=CNCWN&destination=baltic&date_from=2016-01-24&date_to=2016-01-25"
```

Response:
```bash
[
  {
    "average_price": "1121", 
    "date": "2016-01-24"
  }, 
  {
    "average_price": "1101", 
    "date": "2016-01-25"
  }
]

```

# Notes

## Schema modified

`rates_modified.sql` rather than `rates.sql` is used in order to include an auto-increment primary key for the `prices` table:

```sql
CREATE TABLE prices (
    id SERIAL PRIMARY KEY,
    orig_code text NOT NULL,
    dest_code text NOT NULL,
    day date NOT NULL,
    price integer NOT NULL
);
```

That is the only difference between the files.

## Assumption: New codes or slugs would be processed by the API

The API assumes no new slugs or codes (e.g., `united_states` or `GAGEH`) will be encountered while averages are being calculated.

This assumption allows me to cache the slug hierarchy and each slug's direct ports before the first request in order to avoid redundant querying.

The full API implementation would update the cache upon encountering a new slug or code.