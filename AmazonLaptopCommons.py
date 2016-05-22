#!/usr/bin/env python3.5
import json
import re
from bs4 import BeautifulSoup
from collections import namedtuple
from enum import Enum
from AsyncBaseCrawler import BaseAsyncCrawler
from AsyncCrawlerUtils import parsermethod, ParserType, QueuingTask
import asyncio

class PageType(Enum):
    laptoplist_page = 1
    laptopitem_page = 2
    laptopcomment_page = 3
    
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


class LaptopCrawler(BaseAsyncCrawler):

    base_url = "http://www.amazon.com"
    REQUEST_HEADERS = {
        'Host': "www.amazon.com",
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Cookie': 'p90x-info=AFF; x-wl-uid=1kb5U5f5c4rHaG4vz5zIWJu/tVAITMao2+trg9pgrg2fTKafMpUBUPkUqOuAjAIDQar3g8DV8B93eymfW+V36W9Jvd3BZaD+VnsW6BE6SBzwm+DvlwkMoQNBUTu2uqsvrf2Fq+4dOFPU=; session-token="3lAwr9G8TrLsJQD1W/uJPnaHRzyCKNO9Z2BPuj8VV3R6sBSx2+rux3gFClgxJRlut2Sh/P/BtwmpfCKlNPy00879qZbyLITRNtUvaAktIiY86+AOyco9bxIHOfDdsd4uNeNhKAEOqHAAZyJNxZpHI6f4LVeylpK2Q7sqkiC8yWqQGihtw8J/yoyod12CbhwYfOQFytY7CENpCtQvmaTThw=="; x-amz-captcha-1=1462954478411556; x-amz-captcha-2=T6VRd5hpQ0PRa1ut01x7Kw==; csm-hit=s-0ZBGJ0SBMQ9BW3JSM2H8|1463111917503; ubid-main=188-1376416-9392823; session-id-time=2082787201l; session-id=190-0901353-9801359'
    }
 
    @parsermethod(ParserType.GENERATOR, 'laptop_list')
    def parse_laptoplist(self, text):
        """
        This method takes the text of HTML text content.
        Parse the page: extract asin of each laptop item,
        Create a fetching task for each item if there is
        any, Create a fetch task for next list page if 
        thre us any.
        
        Args:
            tasks: fetch task list(Share memory)
            text: HTML text content
            
        Return:
            None
        """
        
        todo = []
        done = []
        
        soup = BeautifulSoup(text, 'html.parser')
        items = [item.find('a') for item in soup.find_all("li", id=re.compile("^result_"))]
                
        """
        add item links
        """
        
        for item in items:
            url = item['href']
            info_item = LaptopInfoItem()
            info_item.asin = re.findall(r'\/B[0-9A-Z]{9}\/', url)[0][1:-1]
            todo.append(
                QueuingTask(url, 'detail_page', info_item)
            )
            
        """
        add next page link
        """
        next_page_links = soup.select(selectorOf['next_page_link'])
        if len(next_page_links):
            next_page_url = next_page_links[0]['href']
            todo.append(
                QueuingTask(LaptopCrawler.base_url+next_page_url, 'laptop_list', LaptopInfoItem())
            )
        else:
            print('CAN NOT REACH NEXT PAGE')
        
        return todo, done
    
    @parsermethod(ParserType.APPENDER, 'detail_page')
    def parse_laptopitem(self, text, info_item):
        """
        (1) parse all the basic information about a laptop model:
            (a) asin serial number
            (b) model title
            (c) rating
            (d) price
            (e) brand
        (2) parse the link to comment list page(add to queue).
        """        
              
        todo, done = [], []
              
        soup = BeautifulSoup(text, 'html.parser')
        title_tags = soup.select(selectorOf['product_title'])
        if len(title_tags):
            info_item.title = title_tags[0].string.strip()
        else:
            print("cannot parse product title of " + info_item.asin)
        
        brand_tags = soup.select(selectorOf['product_brand'])
        if len(brand_tags):
            info_item.brand = brand_tags[0].string.strip()    
        else:
            print("cannot parse product brand of " + info_item.asin)
        
        rating_tags = soup.select(selectorOf['product_rating'])
        if len(rating_tags):
            info_item.rating = rating_tags[0].string.strip()
        else:
            print("cannot parse product rating of " + info_item.asin)
        
        price_tags = soup.select(selectorOf['product_price'])
        if len(price_tags):
            info_item.price = price_tags[0].string.strip()
        else:
            print("cannot parse product price of " + info_item.asin)
           
        comment_links = soup.select(selectorOf['comment_page_link'])
        if len(comment_links):
            url = comment_links[0]['href']
            todo.append(
                QueuingTask(url, 'detail_page', info_item)
            )
        else:
            print("no comments page found for " + info_item.asin + ".")
            print(info_item.asin + " has finished.")
            print(str(info_item))
            done.append(info_item)
            
        return todo, done
        
    @parsermethod(ParserType.APPENDER, 'comments_page')
    def parse_laptopcomments(self, text, info_item):
        """
        (1) parse all the comments:
            (a) customer name
            (b) rating
            (c) comment title
            (d) comment body
        (2) parse the link to next comment list page(add to queue).
        """
        
        todo, done = [], []
        
        soup = BeautifulSoup(text, 'html.parser')
        
        """
        parse all comments 
        """
        for cmmt_soup in soup.select(selectorOf['comment_item']):
            cmmt_item = CommentItem()
            try:
                cmmt_item.rating = cmmt_soup.select(selectorOf['product_rating_in_comment'])[0].string.strip()
                cmmt_item.customer_name = cmmt_soup.select(selectorOf['customer_name'])[0].string.strip()
                cmmt_item.comment_title = cmmt_soup.select(selectorOf['comment_title'])[0].string.strip()
                cmmt_item.comment_body = " ".join([s.strip() for s in cmmt_soup.select(selectorOf['comment_body'])[0].strings])
            except:
                print("ERROR WHEN PARSE " + info_item.asin + "'S COMMENT")
            else:
                info_item.comments.append(cmmt_item)
                
        try:
            next_page_url = soup.select(selectorOf['comment_next_page_link'])[0]['href']
        except IndexError:
            print(info_item.asin + " has finished.")
            print(str(info_item))
            done.append(info_item)
        else:
            todo.append(
                QueuingTask(LaptopCrawler.base_url+next_page_url, 'comments_page', info_item)
            )
            
        return todo, done


if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    seed = "http://www.amazon.com/s/ref=s9_acss_bw_cg_lgopc_2b1?node=13896617011&brand=Dell&lo=computers&pf_rd_m=ATVPDKIKX0DER&pf_rd_s=unified-hybrid-12&pf_rd_r=1RW9GAG72X5T22DTE9XS&pf_rd_t=101&pf_rd_p=2475582802&pf_rd_i=13896617011"
    crawler = LaptopCrawler(QueuingTask(seed, 'laptop_list', LaptopInfoItem()))    

    #print(crawler.__mapping__)
    #print(crawler.__dict__)

    try:
        loop.run_until_complete(crawler.crawl())  # Crawler gonna crawl.
    except KeyboardInterrupt:
        #sys.stderr.flush()
        print('\nInterrupted\n')
        crawler.close()
        #f.close()
    finally:
        crawler.close()

        # next two lines are required for actual aiohttp resource cleanup
        loop.stop()
        loop.close()
