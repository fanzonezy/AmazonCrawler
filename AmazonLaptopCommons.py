import json
import pytesseract 
from sys import stderr
from urllib.request import urlretrieve
from bs4 import BeautifulSoup
try: 
    import Image
except ImportError:
    from PIL import Image
from collections import namedtuple
from enum import Enum

class PageType(Enum):
    laptoplist_page = 1
    laptopitem_page = 2
    laptopcomment_page = 3
    
QueuingTask = namedtuple('QueuingTask', ['url', 'page_type', 'info_item'])

class QandA(object):
    def __init__(self):
        self.question = ""
        self.answer = ""
        
    def __str__(self):
        res = ""
        res += "question:" + self.question
        res += "answer:" + self.answer
        
class CommentItem(object):
    def __init__(self):
        self.rating = ""
        self.customer_name = ""
        self.comment_title = ""
        self.comment_body = ""

    @staticmethod
    def to_dict(item):
        return {
            'rating': item.rating,
            'customer_name': item.customer_name,
            'comment_title': item.comment_title,
            'comment_body': item.comment_body
        }

    def __str__(self):
        return json.dumps(self, default = CommentItem.to_dict)

class LaptopInfoItem(object):
    def __init__(self):
        self.asin = ""
        self.title = ""
        self.brand = ""
        self.price = ""
        self.rating = ""
        self.comments = []
        #self.questions = []
        
    @staticmethod
    def to_dict(item):
        return {
            'asin': item.asin,
            'title': item.title,
            'brand': item.brand,
            'price': item.price,
            'rating': item.rating,
            'comments': [CommentItem.to_dict(comment) for comment in item.comments]
        }
        
    def __str__(self):
        return json.dumps(self, default=LaptopInfoItem.to_dict)
          
          

              
selectorOf = {
    'all_laptop_items': 'li[id^=result_] > div > div:nth-of-type(3) > div > a',
    'next_page_link':'#pagnNextLink',
    'product_title':'#productTitle',
    'product_brand':'#brand',
    'product_rating':'#reviewStarsLinkedCustomerReviews > i > span',
    'product_price':'#priceblock_ourprice',
    'comment_page_link':'#revF > div > a',
    'comment_item':'#cm_cr-review_list > div.a-section.review',
    'product_rating_in_comment':'div:nth-of-type(1) > a:nth-of-type(1) > i',
    'customer_name':'div:nth-of-type(2) > span.a-size-base.a-color-secondary.review-byline > a',
    'comment_title':'div:nth-of-type(1) > a.a-size-base.a-link-normal.review-title.a-color-base.a-text-bold',
    'comment_body':'div:nth-of-type(4) > span',
    'comment_next_page_link':'#cm_cr-pagination_bar > ul > li.a-last > a'
} 

