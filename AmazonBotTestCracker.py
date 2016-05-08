import pytesseract 
try: 
    import Image
except ImportError:
    from PIL import Image

class BotTestCraker(object):
    @staticmethod
    def crack(soup):
        