# holioff-data

Holiday data for the [Holioff](https://github.com/ikutayuska) iPhone alarm app
("祝日はオフになるアラーム"). The app ships a copy of `v1/` and downloads newer
files from GitHub Pages:

```
https://ikutayuska.github.io/holioff-data/v1/index.json
https://ikutayuska.github.io/holioff-data/v1/<REGION>.json   e.g. JP.json
```

## How it is updated

`generate_holidays.py` turns the open-source [holidays](https://github.com/vacanza/holidays)
Python library into one JSON file per ISO 3166-1 country plus `index.json`.
The *Update holiday data* workflow runs it on the 1st of every month (and on
demand from the Actions tab) with the newest `holidays` release, and commits
`v1/` only when a holiday actually changed, so the `generated` date in each file
means "the holidays changed on this date".

To run it locally:

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python tools/publish.py            # default: last year .. two years ahead
.venv/bin/python tools/publish.py --years 2025-2028
```

The same generator lives in the app repository (`Tools/generate_holidays.py`);
keep the two copies identical.

## File format (schema 1)

```json
{
  "schema": 1,
  "region": "JP",
  "generated": "2026-10-20",
  "defaultLanguage": "ja",
  "years": [2025, 2026, 2027, 2028],
  "subdivisions": {},
  "holidays": [
    {"date": "2026-11-03", "type": "public", "names": {"ja": "文化の日", "en": "Culture Day"}}
  ]
}
```

`type` is `public`, `bank`, `school`, `optional`, `government`, `half_day`,
`armed_forces`, `catholic`, `chinese`, `christian`, `hebrew`, `hindu`, `islamic`
or `unofficial`; the app treats only `public` as a day off by default. An entry
with a `subdivisions` array applies only in those states or provinces.

## License

The JSON files are generated from the `holidays` library (MIT License,
Copyright (c) Vacanza Team and individual contributors, dr-prodigy, ryanss) and
are provided under the same license. See `LICENSE`.
