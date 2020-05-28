# Pod⭐

## Design

### Potential Applications

Some quick, product-level thinking about the library to identify and weigh objectives.

**Usage: Command-Line Applications**

Supporting a command-line interface for user-facing operation.

+ Operations need to support introspection or low result latency to drive the user interface smoothly. Users shouldn't have to wait for an entire feed to download and be parsed before seeing metadata, for example.
+ Convenience methods that allow for inspection of feed, episode, and audio metadata.

**Usage: Scraping/Aggregation Infrastructure**

For scraping or aggregating large numbers of feeds at once – potentially in parallel, within a single worker process, or spread across several processes and machines.

+ Robustness to failures at transport and application layers.
+ Good internal logging and mechanisms for identifying and extracting partial failures for later analysis.
+ Minimization of network traffic (likely the most time-consuming operations).
+ Minimal memory usage.
+ Support for "parallelism" (such as it is in Python).

### Objectives

+ Basic criteria:
    + operates as specified;
    + clean design;
    + good readability, extensibility, and maintainability;
    + robust and and resilient to common faults;
    + reasonably performant for a production scenario.
+ At a high level, optimizing for (in order):
    1. performance and robustness
    2. minimization of data transfer
    3. ergonomics
    4. comprehensive functionality

### Considerations

Factors that should be considered in the design and implementation of the library:

+ RSS feeds that have been around for a while (or those with a significant amount of metadata) may be several megabytes in size. Network traffic and memory consumption should be minimized wherever possible.
+ RSS 2.0 feeds may implement ATOM pagination extensions as described in [IETF RFC 5005](https://tools.ietf.org/html/rfc5005#page-12) _Feed Paging and Archiving_.

### Notes

Notes about implementation decisions, etc. as they arise.

+ In FeedPage, we ignore links with rel='prev' because we can emulate that 
functionality locally, and parsing for more than one `<link>` means that there's a chance that we can't _stop_ parsing until we've read the entire file.
+ The development of `Seeker` is useful for a couple of reasons: when used in front of a socket, it minimizes the amount of traffic going over the network for operations that use data closer to the start of a file (i.e. parsing an RSS feed for basic properties); when used in conjunction with an enclosure file, it could allow file attributes to be extracted without reading the entire file.

### Test Data

It occurs to me that it probably makes sense to have a variety of test feeds that I can use to validate robustness.

+ [Missing Richard Simmons](https://rss.prod.firstlook.media/missingrichardsimmons/podcast.rss) – Random feed.
+ [George W. Bush's Speeches/Remarks](https://georgewbush-whitehouse.archives.gov/rss/speeches.xml) – Extremely long-running, with over 1,197 episodes.
+ [Giant Bomb](https://www.giantbomb.com/podcast-xml/giant-bombcast) – Large, with scraper-blocking.
+ [Embedded.FM](http://makingembeddedsystems.libsyn.com/rss) – Reasonbly large feed (~300 episodes) without too much metadata.
+ [CRE: Technik, Kultur, Gesellschaft](http://cre.fm/feed/mp3/) – Foreign language, reasonably-large, implements IETF RFC 5005 pagination.