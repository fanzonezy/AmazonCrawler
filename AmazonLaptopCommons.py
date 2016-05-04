import json

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
        return json.dumps(self, default = CommentItem.to_dict, indent=4)

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
            'title': item.title,
            'brand': item.brand,
            'price': item.price,
            'rating': item.rating,
            'comments': [CommentItem.to_dict(comment) for comment in item.comments]
        }
        
    def __str__(self):
        return json.dumps(self, default=LaptopInfoItem.to_dict, indent=4)
                
selectorOf = {
    'all_laptop_items': '#s-results-list-atf > li > div > div:nth-of-type(3) > div.a-row.a-spacing-none > a',
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

common_headers = {
    #GET /Acer-Chromebook-CB3-131-C3SZ-11-6-Inch-Dual-Core/product-reviews/B019G7VPTC/ref=cm_cr_dp_see_all_btm?ie=UTF8&showViewpoints=1&sortBy=recent HTTP/1.1
    'Host': 'www.amazon.com',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Upgrade-Insecure-Requests': 1,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Avail-Dictionary': 'tKUA8sqv',
    'Accept-Language': 'en-US,en;q=0.8',
} 