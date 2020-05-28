class PodstarError(Exception):
    """
    The base class of exceptions specific to Podstar.
    """
    pass


class ParsingError(PodstarError):
    """
    Raised when an error is encountered when parsing known XML attributes of a 
    feed or its items.

    Attributes:
        tag (str): the improperly-formatted tag
        sourceline (str): the line on which the improperly-formatted tag was 
            encountered within the file
        ex (Exception): the exception raised while attempting to parse the tag
    """

    def __init__(self, tag, sourceline, ex):
        self.tag = tag
        self.sourceline = sourceline
        self.ex = ex


class FeedRequestError(PodstarError):
    """
    Raised when a Feed encounters an unexpected response to an HTTP request.

    Attributes:
        resp (requests.Response): the requests.Response instance
        msg (str): an explanatory message
    """
    
    def __init__(self, resp, msg):
        self.resp = resp
        self.msg = msg