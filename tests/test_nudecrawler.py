from nudecrawler.page import Page
import nudecrawler.verbose 

empty = 'https://telegra.ph/empty-04-03'
belle_delphine = 'https://telegra.ph/belle-delphine-01-16'
sasha_grey = 'https://telegra.ph/sasha-grey-04-18'

nudecrawler.verbose.verbose = True

class TestBasic():

    def test_empty(self):
        p = Page(empty, detect_image=':nude')
        p.check_all()
        assert p.status().startswith('INTERESTING'), "Bad status!"
        print(p)

    def test_belle(self):
        p = Page(belle_delphine, detect_image=':true')
        p.check_all()
        assert p.status().startswith('INTERESTING'), "Bad status!"
        print(p)
