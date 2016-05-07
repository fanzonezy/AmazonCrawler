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
        self._total_connection_made = 0
        self._max_comment_cnt = 200
        
    def connect(self, url, max_retry = 10):
        retry_cnt = max_retry
        html = requests.get(url)
        print(html.content)
        self._total_connection_made += 1
        #print(self._total_connection_made)
        while retry_cnt and not html:
            html = requests.get(url)
            self._total_connection_made += 1
            #print(self._total_connection_made)
            retry_cnt -= 1
        else:    
            if retry_cnt == 0 and not html:
                raise CannotGetPageError("{0} can not be reached.".format(url))
            else:
                return html 
        
    def traverse(self):
        '''
        type: None
        rtype: None
        usage: top level method for traversing all laptop items
        '''
        for seed in self._seeds:
            '''
            try to connect to the 1st Laptop list page
            '''
            try:
                list_page = self.connect(seed)
            except CannotGetPageError as e:
                print(e)
                continue
            except Exception as e:
                print('tarverse')
                print(e)
                continue
                
            '''
            parse the 1st list page
            '''
            soup = BeautifulSoup(list_page.text, 'html.parser')
            self.parse_list(soup)
            
            '''
            keep going to the next list page util reach the last list page 
            '''
            # find the link 
            next_page_link = soup.select(selectorOf['next_page_link'])
            while next_page_link:
                # get the url of the next page    
                url = self._base_url + next_page_link[0]["href"]
                # connect
                try:
                    list_page = self.connect(url)
                except CannotGetPageError as e:
                    print(e)
                    break
                except Exception as e:
                    print('tarverse')
                    print(e)
                    break
                    
                '''    
                parse the this page
                '''
                soup = BeautifulSoup(list_page.text, 'html.parser')
                self.parse_list(soup)
                next_page_link = soup.select(selectorOf['next_page_link'])
                
    def parse_list(self, soup):
        '''
        get the <a> tag which contains the link to the item information page
        '''
        items = soup.select(selectorOf['all_laptop_items'])
        
        '''
        for each item in list page, go to its detail page and parse the item
        '''
        for item in items:
            url = item["href"]
            asin = url.split('/')[-1]
            #print(asin)
            
            try:
                item_info = self.connect(url)
            except CannotGetPageError as e:
                print(e)
                continue
            except Exception as e:
                print('parse list')
                print(e)
                continue
                
            '''
            where reached, parse this item
            '''
            item_soup = BeautifulSoup(item_info.text, 'html.parser')
            self.parse_item(item_soup, asin)
            self._cnt += 1
            
    def parse_item(self, soup, asin):
        '''
        get the basic information 
        '''
        info_item = LaptopInfoItem()
        info_item.asin = asin
        
        print(asin+" begins")
        
        try:
            info_item.title = soup.select(selectorOf['product_title'])[0].string
            info_item.brand = soup.select(selectorOf['product_brand'])[0].string
            info_item.rating = soup.select(selectorOf['product_rating'])[0].string
            info_item.price = soup.select(selectorOf['product_price'])[0].string
        except:
            print('NO:{0}, ASIN:{1}, CONN_SO_FAR:{2}'.format(self._cnt, info_item.asin, self._total_connection_made))
            return
        
        '''
        parse all the comments for each laptop item
        '''             
        try:
            #go to comments page
            comments_page = self.connect(soup.select(selectorOf['comment_page_link'])[0]['href'])
        except CannotGetPageError as e:
            print(e)
            print('NO:{0}, ASIN:{1}, CONN_SO_FAR:{2}'.format(self._cnt, info_item.asin, self._total_connection_made))
            return 
        except Exception as e:
            print("parse_item")
            print(e)
            print('NO:{0}, ASIN:{1}, CONN_SO_FAR:{2}'.format(self._cnt, info_item.asin, self._total_connection_made))
            return

         
        '''    
        parse page and extract comments
        '''
        comments_soup = BeautifulSoup(comments_page.text, 'html.parser')
        info_item.comments.extend(self.parse_comment_list(comments_soup))
        
        next_page_link = comments_soup.select(selectorOf['comment_next_page_link'])

        while next_page_link:
            url = self._base_url + next_page_link[0]['href']
            try:
                comments_page = self.connect(url)
            except CannotGetPageError as e:
                print(e)
                break
            except Exception as e:
                print(e)
                break

            
            '''    
            parse page and extract comments
            '''
            comments_soup = BeautifulSoup(comments_page.text, 'html.parser')
            info_item.comments.extend(self.parse_comment_list(comments_soup))
            
            '''
            check if current comments count is greater than the limit
            '''
            if len(info_item.comments) >= self._max_comment_cnt:
                break
            
            next_page_link = comments_soup.select(selectorOf['comment_next_page_link'])
            
        print('NO:{0}, ASIN:{1}, CONN_SO_FAR:{2}'.format(self._cnt, info_item.asin, self._total_connection_made))
                
    def parse_qa_list(self, soup):
        pass
    
    def parse_qa_item(self, soup):
        pass
    
    def parse_comment_list(self, soup):
        item_list = []
        for comment_item_soup in soup.select(selectorOf['comment_item']):
            item_list.append(self.parse_comment_item(comment_item_soup))    
        return item_list
            
    def parse_comment_item(self, soup):
        item = CommentItem()
        
        try:
            item.rating = soup.select(selectorOf['product_rating_in_comment'])[0].string
            item.customer_name = soup.select(selectorOf['customer_name'])[0].string
            item.comment_title = soup.select(selectorOf['comment_title'])[0].string
            item.comment_body = " ".join([s for s in soup.select(selectorOf['comment_body'])[0].strings])
        except:
            pass
        
        return item
      
crawler = LaptopCrawler()
crawler.traverse()
        
