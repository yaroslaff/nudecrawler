class NudeCrawlerException(Exception):
    pass

class BoringImage(NudeCrawlerException):
    """ Image is boring, no need to analyse, e.g. small icon """
    pass

class ProblemImage(NudeCrawlerException):
    """ Technical problem with image, e.g. 404 NotFound or damaged file """
    pass

