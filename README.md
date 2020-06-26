# Pod⭐

_Podstar_ is a Python library for working with podcasts. It optimizes for robustness, efficiency, and standards support while providing a clean and simple API. Podstar has some neat features:

+ robust parsing of RSS-based podcast feeds
+ transparent use of paginated feeds (via RSS pagination)
+ support for HTTP caching headers (`ETag` or `Last-Modified`), enabling long-running aggregator processes to request as little data as possible
+ easy access to audio information, including:
  + duration (as determined by iTunes DTD metadata when available, or by streaming audio files to memory until necessary metadata is available)
  + bitrate
  + sample rate

## Getting Started

Ensure that you've got Python `>= 3.3` installed, and a new Python virtual environment activated. Install the library using:

```sh
$ pip install podstar
```

You're done!

## Using Podstar

The following code iterates over a podcast feed, listing each episode and its duration:

```python
import time
import podstar

feed = podstar.Feed('http://feeds.sceneonradio.org/SceneOnRadio')

# print some information about the podcast, including a text description (HTML in the description will be removed automatically)
print(feed.title)
print(feed.description + "\n")

# list each episode with its title, date published, and duration
for episode in feed.episodes():
    pub_date = episode.published_at.strftime("%a %b %d, %Y")
    duration = time.strftime("%H:%M:%S", time.gmtime(episode.duration))
    print(f"– \"{episode.title}\" ({pub_date}) [{duration}]")
```

For further examples of how to use Podstar, see the `examples/` directory.

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
