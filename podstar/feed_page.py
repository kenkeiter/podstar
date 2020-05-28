import tempfile
import datetime
import logging

import requests
import lxml.etree

from podstar import stream
from podstar import episode
from podstar import errors


logger = logging.getLogger(__name__)


class FeedPage(object):
    """
    FeedPage encapsulates a single page of an (optionally) multi-page RSS 
    feed, and provides transparent caching and iterative parsing of feed 
    properties and episodes.

    Notes:
        When support for server-side cache helpers (either ETags or 
        Modified-Since) are detected, they will be used. If both are available 
        ETags will be preferred.

        The XML parsing of FeedPage is "loose"; the intention is to allow for 
        as much deviation of feeds from standards as possible while still 
        providing consistent information to library users.
    """

    def __init__(self, feed, url, robust=True, episode_cls=episode.Episode):
        self._feed = feed
        self._url = url
        self._robust = robust
        self._episode_cls = episode_cls

        self._log = logger.getChild("{cls_name}.{id}".format(
            cls_name=self.__class__.__name__,
            id=id(self)))

        self._cache_reset()

    ###
    # Cache-Related Helpers
    ###

    def _cache_reset(self):
        self._log.debug("Resetting caches.")
        self._next_page = None

        self._episodes = None
        self._all_episodes_cached = False

        self._cache_raw = None
        self._cache_etag = None
        self._cache_last_modified = None
        self._cache_expires = None

    def _cache_cleanup(self):
        if self._parsing_complete:
            self._log.debug("Parsing is complete. Closing Seeker.")
            if self._cache_raw is not None:
                self._cache_raw.close()
            self._cache_raw = None

    @property
    def _parsing_complete(self):
        c = (self._all_episodes_cached and self._next_page is not None)
        return c

    @staticmethod
    def _http_response_expiration(headers, now):
        # prefer Cache-Control over Expires
        if 'Cache-Control' in headers:
            fields = (v.strip() for v in headers['Cache-Control'].split(','))
            for field in fields:
                # if anything's marked as no-store or no-cache, assume we can't 
                # cache anything in the body
                if field == 'no-store' or field.startswith('no-cache'):
                    return None
                elif field.startswith('max-age'):
                    _, duration = field.split('=')
                    return now + datetime.timedelta(seconds=int(duration))
        
        # handle Expires header, if Cache-Control wasn't found
        elif 'Expires' in headers:
            # the Expires header comes in two flavors, RFC 1123 and RFC 850
            exp = None
            try:
                exp = datetime.datetime.strptime("%a, %d %b %Y %H:%M:%S GMT")
            except ValueError:
                try:
                    exp = datetime.datetime.strptime(
                        "%A, %d-%b-%y %H:%M:%S GMT")
                except ValueError:
                    pass
            return exp

        # otherwise, if no expiration was provided, return None
        return None

    @property
    def is_cached(self):
        return (self._cache_raw is not None)

    @property
    def expired(self):
        return self._cache_expires is None or \
            (self._cache_expires is not None and \
            datetime.datetime.now() > self._cache_expires)

    ###
    # Feed Data Manipulation
    ###

    @property
    def _data(self):
        """
        Return a SeekableCache tied to underlying raw data as requested from 
        the server.
        """
        # if the cache hasn't been filled, or if it's not expired, return it
        if self._cache_raw:
            return self._cache_raw
        
        # use headers to avoid requesting unchanged content
        headers = {}
        if self._cache_etag:
            headers['If-Not-Match'] = self._cache_etag
        elif self._cache_last_modified:
            headers['If-Modified-Since'] = self._cache_last_modified

        # make a request for the XML of the feed
        self._log.debug("Updating feed data if required...")
        resp = self._feed._request(
            method='GET', 
            url=self._url, 
            headers=headers,
            allow_redirects=True, 
            stream=True)

        # if the data has not been modified since we last requested it, 
        # simply return the cached version
        if resp.status_code == 304:
            self._log.debug("Feed data is not stale.")
            return self._cache_raw

        # otherwise, if we received a non-OK response, raise an exception
        if not 199 < resp.status_code < 300:
            raise errors.FeedRequestError("Invalid status code.")

        # save any returned cache identifiers
        self._cache_etag = resp.headers.get('ETag', None)
        self._cache_last_modified = resp.headers.get('Last-Modified', None)

        # determine an expiration date for our cache, if it's provided
        self._cache_expires = self._http_response_expiration(
            resp.headers, datetime.datetime.now())

        self._log.debug(
            "Updated feed data to ETag %s (or Last-Modified %s).",
            self._cache_etag, self._cache_last_modified,)
        
        # wrap the file-like raw item in a stream.Seeker to use as our cache
        resp.raw.decode_content = True
        self._cache_raw = stream.Seeker(resp.raw)

        # return the newly created cache
        return self._cache_raw

    def _iterparse(self, *args, **kwargs):
        # ensure that data is rewound
        data = self._data
        data.seek(0)
        return lxml.etree.iterparse(data, *args, **kwargs)

    def _discover_next_page(self):
        for _, el in self._iterparse():
            # skip anything that's not a link whose direct ancestor is channel
            if (not el.tag.lower().endswith('link')) or \
                (el.getparent().tag.lower() != 'channel'):
                    el.clear()
                    continue
            
            # if it doesn't have the required rel/href attributes, it's not 
            # we're looking for
            rel = el.attrib.get('rel', None)
            href = el.attrib.get('href', None)
            if rel is None or href is None:
                el.clear()
                continue
            
            # normalize attributes, because anybody can write a feed generator
            rel = rel.lower().strip()

            # build a FeedPage and exit the generator early, ensuring we read 
            # the minimum amount of data required
            if rel == 'next':
                return self.__class__(
                    feed=self._feed,
                    url=href.lower().strip(), 
                    episode_cls=self._episode_cls)

        # if no other pages are found, indicate that fact internally
        return False

    ###
    # Primary Public Functionality
    ###

    @property
    def url(self):
        return self._url

    @property
    def next_page(self):
        """
        Return the next page in the feed, if there is one.

        Returns:
            If a next page is defined by the feed, a new instance of the 
            current __class__ representing the next page will be returned; 
            otherwise, `None` will returned.
        """
        # discover pages if they haven't already been discovered in this cycle
        if self._next_page is None:
            self._next_page = self._discover_next_page()
            # clean up the cache if necessary
            self._cache_cleanup()
        
        # convert false to none for user's benefit
        if self._next_page == False:
            return None
        
        return self._next_page

    def channel_property(self, tag, default=None):
        for _, el in self._iterparse():
            if el.tag == tag:
                return el.text
        return default

    def episodes(self, cache=True):
        """
        Iterate over episodes contained within this page of the feed.
        
        Arguments:
            cache (bool): enable or disable caching of extracted Episodes

        Yields:
            episode.Episode: an episode extracted from the feed

        Notes:
            Episodes will be cached as they are extracted, and will be ignored 
            if they are already in the cache (as determined by their uuid). 
            If not all data has been read from the server before the connection 
            was closed and no cache comparison mechanism was provided (i.e. 
            ETag or Last-Modified), all caches will be invalidated. 
            
            If all valuable information been cached (pages, episodes, etc.), we 
            can get clear the data buffer.
        """
        if cache:
            self._episodes = self._episodes or {}

            # hit cache first, if it contains episodes
            if len(self._episodes) > 0:
                for ep in self._episodes.values():
                    yield ep

            # if we already have everything in the cache, we're done here
            if self._all_episodes_cached:
                return

        for _, el in self._iterparse():
            if el.tag.lower() == 'item':
                # TODO(kk): Add exception handling here.
                ep = self._episode_cls.from_xml_item(
                    self._feed, el, self._robust)
                el.clear()

                # hash is already used for dictionary lookup, and is used as 
                # a key function here across the combination of the required 
                # attributes of the item
                cache_key = hash(str(ep.title) + str(ep.description))
                
                if cache and (cache_key not in self._episodes):
                    self._episodes[cache_key] = ep
                
                yield ep

        # if we've iterated through all episodes and caching is enabled, all 
        # episodes have now been cached
        if cache:
            self._all_episodes_cached = True

        # clean up the cache if necessary
        self._cache_cleanup()
