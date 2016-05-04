import requests
from AmazonLaptopExceptions import *
from AmazonLaptopCommons import *
from bs4 import BeautifulSoup 

class LaptopCrawler(object):
    def __init__(self):
        self._base_url = "http://www.amazon.com"
        self._visited_url = set()
        self._seeds = [
            "http://www.amazon.com/s/ref=s9_acss_bw_bf_abcdefgh_1_img?rh=i%3Acomputers%2Cn%3A565108&field-availability=-1&field-brandtextbin=Acer&ie=UTF8&pf_rd_m=ATVPDKIKX0DER&pf_rd_s=merchandised-search-10&pf_rd_r=1VQZCF5T7GRS1QFW0TKG&pf_rd_t=101&pf_rd_p=2405855262&pf_rd_i=565108"
            #"http://www.amazon.com/s/ref=amb_link_357131882_10?ie=UTF8&field-availability=-1&field-price-mp-owner-bin=00000-39999&node=565108&pf_rd_m=ATVPDKIKX0DER&pf_rd_s=merchandised-search-left-3&pf_rd_r=1VQZCF5T7GRS1QFW0TKG&pf_rd_t=101&pf_rd_p=2443068342&pf_rd_i=565108",
            #"http://www.amazon.com/s/ref=amb_link_357131882_11?ie=UTF8&field-availability=-1&field-price-mp-owner-bin=40000-99999&node=565108&pf_rd_m=ATVPDKIKX0DER&pf_rd_s=merchandised-search-left-3&pf_rd_r=1VQZCF5T7GRS1QFW0TKG&pf_rd_t=101&pf_rd_p=2443068342&pf_rd_i=565108",
            #"http://www.amazon.com/s/ref=amb_link_357131882_12?ie=UTF8&field-availability=-1&field-price-mp-owner-bin=100000-149999&node=565108&pf_rd_m=ATVPDKIKX0DER&pf_rd_s=merchandised-search-left-3&pf_rd_r=1VQZCF5T7GRS1QFW0TKG&pf_rd_t=101&pf_rd_p=2443068342&pf_rd_i=565108",
            #"http://www.amazon.com/s/ref=amb_link_357131882_13?ie=UTF8&field-availability=-1&field-price-mp-owner-bin=150000-500000&node=565108&pf_rd_m=ATVPDKIKX0DER&pf_rd_s=merchandised-search-left-3&pf_rd_r=1VQZCF5T7GRS1QFW0TKG&pf_rd_t=101&pf_rd_p=2443068342&pf_rd_i=565108"
        ]
        self._cnt = 1
        
    def connect(self, url):
        retry_cnt = 10
        html = requests.get(url)
        while retry_cnt and not html:
            html = requests.get(url)
            retry_cnt -= 1
        else:    
            if retry_cnt == 0 and not html:
                raise CannotGetPageError("{0} can not be reached.".format(url))
            else:
                return html 
        
    def traverse(self):
        res = []
        for seed in self._seeds:
            try:
                # start at getting the page connect of a seed url
                list_page = self.connect(seed)
                soup = BeautifulSoup(list_page.text, 'html.parser')
                # parse the basic information of each laptop on one list page
                res.extend(self.parse_list(soup))
                # go to next page, if there is any
                next_page_link = soup.select(selectorOf['next_page_link'])[0]
                while next_page_link:
                    url = self._base_url + next_page_link["href"]
                    list_page = self.connect(url)
                    soup = BeautifulSoup(list_page.text, 'html.parser')
                    res.extend(self.parse_list(soup))
                    next_page_link = soup.select(selectorOf['next_page_link'])[0]
            except CannotGetPageError as e:
                print(e.value())
            #except Exception as e:
            #    print('tarverse')
            #    print(e)
                
        return res
                
    def parse_list(self, soup):
        parsed_item_list = []
        # get the <a> tag which contains the link to the item information page
        items = soup.select(selectorOf['all_laptop_items'])
        
        for item in items:
            #print("{0}: {1}".format(self._cnt, item["title"]))
            url = item["href"]
            asin = url.split('/')[-1]
            print(asin)
            
            try:
                item_info = self.connect(url)
            except CannotGetPageError as e:
                print(e.value)
            except Exception as e:
                print('parse list')
                print(e)
                
            item_soup = BeautifulSoup(item_info.text, 'html.parser')
            parsed_item_list.append(self.parse_item(item_soup, asin))
            self._cnt += 1
        
        
        return parsed_item_list
        
    def parse_item(self, soup, asin):
        #get the basic information 
        info_item = LaptopInfoItem()
        info_item.title =   soup.select(selectorOf['product_title'])[0].string
        info_item.brand =   soup.select(selectorOf['product_brand'])[0].string
        info_item.rating = soup.select(selectorOf['product_rating'])[0].string
        info_item.price =   soup.select(selectorOf['product_price'])[0].string
        
        #print("{0}, {1}, {2}, {3}".format(info_item.title, info_item.brand, info_item.rating, info_item.price))
                      
        try:
            #go to comments page
            comments_page = self.connect(soup.select(selectorOf['comment_page_link'])[0]['href'])
        except CannotGetPageError as e:
            print("cannot get comments, "+e.value())
        except Exception as e:
            print("parse_item")
            print(e)
            
        # parse page and extract comments
        comments_soup = BeautifulSoup(comments_page.text, 'html.parser')
        info_item.comments = self.parse_comment_list(comments_soup)
          
        print(str(info_item))  
        return info_item
            
    def parse_qa_list(self, soup):
        pass
        #print(soup.select("#a-page > div.a-section.askQuestionListPage > div.a-section.askInlineWidget > div"))
    
    def parse_comment_list(self, soup):
        item_list = []
        for comment_item_soup in soup.select(selectorOf['comment_item']):
            item_list.append(self.parse_comment_item(comment_item_soup))
        return item_list
            
    def parse_qa_item(self, soup):
        pass
    
    def parse_comment_item(self, soup):
        item = CommentItem()
        item.rating = soup.select(selectorOf['product_rating_in_comment'])[0].string
        item.customer_name = soup.select(selectorOf['customer_name'])[0].string
        item.comment_title = soup.select(selectorOf['comment_title'])[0].string
        item.comment_body = " ".join([s for s in soup.select(selectorOf['comment_body'])[0].strings])
        return item
      
crawler = LaptopCrawler()
with open('D:\\acer.txt', 'w') as f:
    for item in crawler.traverse():
        f.write(str(item))
