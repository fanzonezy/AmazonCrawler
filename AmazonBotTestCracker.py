import pytesseract 
from sys import stderr

from urllib.request import urlretrieve
import requests
from bs4 import BeautifulSoup
try: 
    import Image
except ImportError:
    from PIL import Image

class BotTestCracker(object):
    
    AMAZON_BOT_TEST_IMAGE_PATH = "body > div > div.a-row.a-spacing-double-large > div.a-section > div > div > form > div.a-row.a-spacing-large > div > div > div.a-row.a-text-center > img"
    AMAZON_BIT_TEST_FORM_PATH = "body > div > div.a-row.a-spacing-double-large > div.a-section > div > div > form"
    
    TEMP_STORE_PATH = r""
    
    @staticmethod
    def crack(soup):
        #print("CALLED")
        try:
            tag = soup.select(BotTestCracker.AMAZON_BOT_TEST_IMAGE_PATH)[0]
            url = tag["src"]
            path = BotTestCracker.TEMP_STORE_PATH+url.split('/')[-1]
            urlretrieve(url, path)
            im = Image.open(path)
            text = pytesseract.image_to_string(im)
        except Exception as e:
            raise e
            #stderr.write('CANNOT　CRACK THIS TEST.')
        else:
            return text 
        return ""
            
                
            
html = ""
with open("D:\\bottest1.html") as f:
    for line in f:
        html += line
        
BotTestCracker.crack(BeautifulSoup(html, "html.parser"))
        
