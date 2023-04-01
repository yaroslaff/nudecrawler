class ImageCache(object):
    def __init__(self):
        self._sum2v = dict()
        self._url2v = dict()
        
        self.miss_url = 0
        self.miss_sum = 0
        self.hit_url = 0
        self.hit_sum = 0
    
    def url2v(self, url):
        try:
            v = self._url2v[url]
            self.hit_url +=1
            return v
        except KeyError:
            self.miss_url += 1
            return None
            

    def sum2v(self, sum):
        try:
            v = self._sum2v[sum]
            self.hit_sum += 1
            return v
        except KeyError:
            self.miss_sum += 1
            return None
    
    def register(self, url, sum, verdict):
        self._url2v[url] = verdict
        self._sum2v[sum] = verdict
        
    def status(self):
        return {
            'urls': len(self._url2v),
            'sums': len(self._sum2v),
            'hit_url': self.hit_url,
            'hit_sum': self.hit_sum,
            'miss_url': self.miss_url,
            'miss_sum': self.miss_sum
        }
        

cache = ImageCache()
