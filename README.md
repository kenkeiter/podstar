# Pod⭐

_Podstar_ is a Python library for working with podcasts. It optimizes for robustness, efficiency, and standards support while providing a clean and simple API.

Written in a day and a half – so there may be bugs. But there are also tests.

## Getting Started

Ensure that you've got Python `>= 3.3` installed, and a new Python virtual environment activated.

To get started, clone the repository and `cd` to it:

```sh
$ git clone <repo url>
$ cd podstar/
```

Then, install the package by running:

```sh
$ pip install .
```

You should now be able to try fetching episodes of a podcast for a specific date:

```sh
podstar --url="https://rss.prod.firstlook.media/missingrichardsimmons/podcast.rss" --date="2017-02-22"
```

## Development

Getting started with development on Podstar is relatively straightforward. 

Ensure that you have Python `>= 3.3` installed, clone the repository, and `cd` to it

```sh
$ git clone <repo url>
$ cd podstar/
```

Use `pip` to install the dependencies specified in `requirements.txt` (if you haven't already) as well as the development dependencies specified in `dev_requirements.txt`

```sh
$ pip install -r requirements.txt
$ pip install -r dev_requirements.txt
```

To run all tests, execute

```sh
$ python -m pytest tests
```

To check test coverage, execute:

```sh
python -m pytest --cov=podstar --cov-report term-missing -s tests
```

### Examples

`examples/download.py` – The original sketch used when designing the API for this library. Run it from the project's root directory by executing:

```sh
$ python -m examples.sketch
```

`examples/crawl.py` – Parses a good number of feeds in parallel using digitalpodcast.com as a convenient redirect. From the project's root directory, try it (on a decent internet connection) by executing:

```sh
$ python -m examples.crawl
```
