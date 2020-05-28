import collections
from email.utils import parsedate_to_datetime

from podstar import errors
from podstar import enclosure


ItemProperty = collections.namedtuple('ItemProperty', ['attrs', 'text'])


class Episode(object):

    RSS_FIELD_PROCESSORS = {
        'title': lambda el, attrs: attrs.setdefault('title', el.text.strip()),
        'description': lambda el, attrs: \
            attrs.setdefault('description', el.text.strip()),
        'link': lambda el, attrs: attrs.setdefault('link', el.text.strip()),
        'author': lambda el, attrs: attrs.setdefault('author', el.text.strip()),
        'category': lambda el, attrs: \
            attrs['categories'].append(el.text.strip()),
        'comments': lambda el, attrs: \
            attrs.setdefault('comments_link', el.text.strip()),
        'guid': lambda el, attrs: attrs.setdefault('guid', el.text.strip()),
        'pubdate': lambda el, attrs: \
            attrs.setdefault('published_at', 
                parsedate_to_datetime(el.text.strip())),
    }

    @classmethod
    def from_xml_item(cls, feed, item_el, robust=True):
        """
        Parse an XML <item> element to extract salient details and return an 
        correspondingly-instantiated Episode instance.

        Arguments:
            feed (feed.Feed): the feed from which the Episode is being parsed
            item_el (lxml.etree.Element): the XML element representing the 
                <item> tag.
            robust (bool, optional): indicate whether to raise errors when they 
                occur, or accumulate them in the `errors` property of the 
                resulting Episode.

        Returns:
            Episode: an Episode instance (or an instance of the current 
                subclass) containing information extracted from XML.
        """
        attrs = {
            'namespaces': {},
            'categories': [],
            'errors': []}
        
        for el in item_el.iterchildren():
            process = cls.RSS_FIELD_PROCESSORS.get(el.tag.lower(), None)
            if process is None:
                prop = ItemProperty(attrs=el.attrib, text=el.text)
                if el.prefix is not None:
                    ns = el.nsmap[el.prefix]
                    tag = el.tag.rsplit('}', 1)[-1]
                    attrs['namespaces'].setdefault(ns, {})
                    attrs['namespaces'][ns][tag] = prop
                else:
                    attrs[el.tag] = prop
                continue
            
            try:
                process(el, attrs)
            except Exception as e:
                ex = errors.ParsingError(el.tag, el.sourceline, e)
                if not robust:
                    raise ex
                attrs['errors'].append(ex)
        
        return cls(feed, **attrs)

    def __init__(self, feed, title=None, description=None, namespaces={}, 
        errors=[], **kwargs):
        """
        Create a new Episode from attributes.

        Arguments:
            feed (feed.Feed): the feed from which the Episode was parsed
            title (str, optional): the title of the episode
            description (str, optional): a description of the episode
            namespaces (dict, optional): a dictionary of 
                DTD-URL-to-dict<tag:ItemProperty> associations containing 
                additional annotations on the episode from unsupported 
                namespaces
            errors (list, optional): a list of exceptions encountered during 
                parsing of the Episode
            kwargs (dict, optional): additional un-namespaced attributes that 
                should be accessible using the `get` method of the Episode
        """
        self._feed = feed
        self._title = title
        self._description = description
        self._attrs = kwargs
        
        self._namespaces = namespaces
        self._audio = None

        # RSS specification requires an item have a title or description
        if not self._title and not self._description:
            raise ValueError("'title' or 'description' must be included")

    @property
    def audio(self):
        """
        If the episode contains an enclosed audio file, return an 
        AudioEnclosure instance allowing inspection and manipulation of audio.

        Returns:
            enclosure.AudioEnclosure or None
        """
        if self._audio is None: 
            en = self._attrs.get('enclosure', ItemProperty(text='', attrs={}))
            url = en.attrs.get('url', None)
            if url is not None:
                self._audio = enclosure.AudioEnclosure(self._feed, url)
            else:
                self._audio = False

        if self._audio == False:
            return None
        
        return self._audio

    @property
    def soft_duration(self):
        """
        Determine the duration of the audio (in seconds) using available XML 
        metadata, when available.

        Returns:
            float or None: The duration of the enclosed audio in seconds, if 
                it can be determined from parsed data, or None.
        """
        # if the feed has an iTunes dtd, it may be possible to find the episode 
        # duration in that namespace's <duration> tag
        itunes_ns = self.namespaces.get(
            'http://www.itunes.com/dtds/podcast-1.0.dtd', {})
        if 'duration' in itunes_ns:
            duration = itunes_ns['duration'].text.strip()
            # iTunes duration may omit HH: or MM:
            v = list(map(int, duration.split(':')))
            d = sum(n * s for n, s in zip(v[::-1], (1, 60, 3600)))
            return float(d)
        return None

    @property
    def duration(self):
        """
        Determine the duration of the audio (in seconds) using either available 
        XML metadata, or by inspecting the contents of the enclosed audio file, 
        when available.

        Notes:
            Not all audio files support introspection of length without 
            reading the entire file (mpeg-3 files, for example). Using 
            `duration` may result in significant data transfer.

        Returns:
            float or None: the duration of the file, or None if it cannot be 
                determined using available information
        """
        return self.soft_duration or (self.audio and self.audio.duration)

    @property
    def title(self):
        """
        Get the title of the episode if available.

        Returns:
            str or None: the title of the episode, if it is available, or None
        """
        return self._title

    @property
    def description(self):
        """
        Get the description of the episode if available.

        Returns:
            str or None: the description of the episode, if it is available, or 
                None
        """
        return self._description

    @property
    def link(self):
        """
        Get a link to a webpage associated with the episode, if available.

        Returns:
            str or None: the URL, if it is available, or None
        """
        return self._attrs.get('link', None)

    @property
    def author(self):
        """
        Get the author of the episode if available.

        Returns:
            str or None: the author of the episode, if it is available, or None
        """
        return self._attrs.get('author', None)

    @property
    def categories(self):
        """
        Get a list of categories for the episode, if they are specified.

        Returns:
            list or None: a list of strings defining associated categories, or 
                None, if it was omitted
        """
        return self._attrs.get('categories', [])

    @property
    def comments_link(self):
        """
        Get a link to the comments associated with the episode, if available.

        Returns:
            str or None: the URL, if it is available, or None
        """
        return self._attrs.get('comments_link', None)

    @property
    def guid(self):
        """
        Get an ItemProperty containing a GUID for the episode, if provided.

        Returns:
            ItemProperty or None
        """
        return self._attrs.get('guid', None)

    @property
    def published_at(self):
        """
        Get a datetime.datetime representing the date on which the episode was 
        published.

        Returns:
            datetime.datetime or None: a representative datetime.datetime, or 
                None, if no publish date was provided.
        """
        return self._attrs.get('published_at', None)

    @property
    def namespaces(self):
        """
        Get a dictionary of namespaced XML attributes that were extracted 
        during parsing, indexed by their DTD URL.

        Returns:
            dict: a dict containing DTD-URL-to-dict associations, structured 
                dict<dtd:dict<tag:ItemProperty>>
        """
        return self._namespaces

    def get(self, key, default=None):
        """
        Get the value of an attribute for which a convenience property has not 
        been defined.

        Arguments:
            key (str): the name of the attribute
            default (optional): a value to return if the key is not found

        Returns:
            The value at the specified key, or the default value.
        """
        return self._attrs.get(key, default)

    @property
    def errors(self):
        """
        Get a list of exceptions that occurred while parsing the XML that 
        represented this episode.

        Returns:
            list: list of Exceptions
        """
        return self._attrs.get('errors', [])

    def __repr__(self):
        """
        Get an easily-decipherable string representation of the episode.

        Returns:
            str: a nice, readable string
        """
        return "<Episode \"{title_or_desc}\">".format(
            title_or_desc=(self.title or self.description))