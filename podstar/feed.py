import requests
from bs4 import BeautifulSoup

from podstar import feed_page


class Feed(object):

    def __init__(self, url, page_cls=feed_page.FeedPage):
        """
        Create a new Feed instance.

        Arguments:
            url (str): the URL of the first page of the RSS feed
            page_cls (feed_page.FeedPage): FeedPage or a subclass of it; will 
                be used when creating new pages as dictated by the structure of 
                the feed, or when the data contained within a page expires.

        Note:
            RSS data is both lazily and partially fetched, whenever possible. 
            In many cases, parsing feed attributes such as its <title> or 
            <description> will not require fetching the entire RSS resource.
        """
        self._url = url
        self._session = requests.Session()
        self._page_cls = page_cls
        self._first_page = page_cls(self, self._url)

        self._attr_cache = {}

    def _request(self, *args, **kwargs):
        """Make an HTTP request using the feed's session.

        Request additional data using the session defined by the feed.
        """
        return self._session.request(*args, **kwargs)

    def episodes(self, cache=True):
        """
        Get episodes described within the feed.

        Yields:
            Episode: the next episode

        Note:
            Episodes are parsed from each page of the feed lazily, and each 
            page is fetched lazily and partially. This means that successive 
            calls to `episodes` will yield cached Episode instances, and will 
            not make further requests to the server. As such, taking fewer 
            than the total number of episodes from the generator will not cause 
            each page to be downloaded in its entirety.
        """
        # if self._first_page.expired:
            # self._first_page = feed_page.FeedPage(self, self._first_page.url)

        page = self._first_page
        while page is not None:
            for ep in page.episodes():
                yield ep
            page = page.next_page

    def get(self, prop_name, default=None):
        """
        Return the text of a tag that is the direct ancestor of the top-level 
        <channel> by its name.

        Arguments:
            prop_name (str): the name of a tag, such as "title"
            default: an object of any type to return if the property isn't found

        Return:
            The value of the property as a `str`, or if the property cannot be 
            found, the value of the `default` argument.
        """
        
        # if the first page is expired, clear cached attributes -- the next 
        # request for a property will cause a refresh of the underlying source
        if self._first_page.expired:
            self._attr_cache = {}

        if prop_name not in self._attr_cache:
            self._attr_cache[prop_name] = \
                self._first_page.channel_property(prop_name, default)

        return self._attr_cache[prop_name]

    ###
    # Convenience Properties
    ###

    @property
    def url(self):
        return self._url

    @property
    def title(self):
        return self.get('title', '').strip()

    @property
    def description_html(self):
        return self.get('description', '').strip()
    
    @property
    def description(self):
        """
        Get the description of the feed with HTML removed.
        """
        body = self.get('description', '').strip()
        tree = BeautifulSoup(body, 'lxml')
        return tree.get_text()

    @property
    def link(self):
        return self.get('link', '').strip()

    @property
    def language(self):
        return self.get('language', '').strip()

    @property
    def copyright(self):
        return self.get('copyright', '').strip()