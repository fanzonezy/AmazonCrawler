import asyncio
import aiohttp
#import objgraph
import sys
import re
import logging

from multiprocessing import Process, Manager
from bs4 import BeautifulSoup

from AmazonLaptopCommons import PageType, selectorOf, LaptopInfoItem, CommentItem, QueuingTask

try:
    from asyncio import JoinableQueue as Queue
except ImportError:
    from asyncio import Queue

LOGGER = logging.getLogger(__name__)
item_cnt = 0
    
class PageParsers(object):
    base_url = "http://www.amazon.com"
    
    @staticmethod
    def parse_laptoplist(tasks, text):
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
        
        soup = BeautifulSoup(text, 'html.parser')
        items = [item.find('a') for item in soup.find_all("li", id=re.compile("^result_"))]
                
        """
        add item links
        """
        
        for item in items:
            url = item['href']
            info_item = LaptopInfoItem()
            info_item.asin = re.findall(r'\/B[0-9A-Z]{9}\/', url)[0][1:-1]
            tasks.append(
                QueuingTask(url, PageType.laptopitem_page, info_item)
            )
            
        """
        add next page link
        """
        next_page_links = soup.select(selectorOf['next_page_link'])
        if len(next_page_links):
            next_page_url = next_page_links[0]['href']
            tasks.append(
                QueuingTask(PageParsers.base_url+next_page_url, PageType.laptoplist_page, LaptopInfoItem())
            )
        else:
            LOGGER.warning('CAN NOT REACH NEXT PAGE')
        
    @staticmethod
    def parse_laptopitem(tasks, res, text, info_item):
        """
        (1) parse all the basic information about a laptop model:
            (a) asin serial number
            (b) model title
            (c) rating
            (d) price
            (e) brand
        (2) parse the link to comment list page(add to queue).
        """        
              
        soup = BeautifulSoup(text, 'html.parser')
        title_tags = soup.select(selectorOf['product_title'])
        if len(title_tags):
            info_item.title = title_tags[0].string.strip()
        else:
            LOGGER.warning("cannot parse product title of " + info_item.asin)
        
        brand_tags = soup.select(selectorOf['product_brand'])
        if len(brand_tags):
            info_item.brand = brand_tags[0].string.strip()    
        else:
            LOGGER.warning("cannot parse product brand of " + info_item.asin)
        
        rating_tags = soup.select(selectorOf['product_rating'])
        if len(rating_tags):
            info_item.rating = rating_tags[0].string.strip()
        else:
            LOGGER.warning("cannot parse product rating of " + info_item.asin)
        
        price_tags = soup.select(selectorOf['product_price'])
        if len(price_tags):
            info_item.price = price_tags[0].string.strip()
        else:
            LOGGER.warning("cannot parse product price of " + info_item.asin)
           
        comment_links = soup.select(selectorOf['comment_page_link'])
        if len(comment_links):
            url = comment_links[0]['href']
            tasks.append(
                QueuingTask(url, PageType.laptopcomment_page, info_item)
            )
        else:
            LOGGER.warning("no comments page found for " + info_item.asin + ".")
            print(info_item.asin + " has finished.")
            res.append(info_item)
        
    @staticmethod
    def parse_laptopcomments(tasks, res, text, info_item):
        """
        (1) parse all the comments:
            (a) customer name
            (b) rating
            (c) comment title
            (d) comment body
        (2) parse the link to next comment list page(add to queue).
        """
        
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
                LOGGER.warning("ERROR WHEN PARSE " + info_item.asin + "'S COMMENT")
            else:
                info_item.comments.append(cmmt_item)
                
        try:
            next_page_url = soup.select(selectorOf['comment_next_page_link'])[0]['href']
        except IndexError:
            print(info_item.asin + " has finished.")
            res.append(info_item)
        else:
            tasks.append(
                QueuingTask(PageParsers.base_url+next_page_url, PageType.laptopcomment_page, info_item)
            )
            
class AsyncCrawler(object):
    
    REQUEST_HEADERS = {
        'Host': "www.amazon.com",
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Cookie': 'p90x-info=AFF; x-wl-uid=1kb5U5f5c4rHaG4vz5zIWJu/tVAITMao2+trg9pgrg2fTKafMpUBUPkUqOuAjAIDQar3g8DV8B93eymfW+V36W9Jvd3BZaD+VnsW6BE6SBzwm+DvlwkMoQNBUTu2uqsvrf2Fq+4dOFPU=; session-token="3lAwr9G8TrLsJQD1W/uJPnaHRzyCKNO9Z2BPuj8VV3R6sBSx2+rux3gFClgxJRlut2Sh/P/BtwmpfCKlNPy00879qZbyLITRNtUvaAktIiY86+AOyco9bxIHOfDdsd4uNeNhKAEOqHAAZyJNxZpHI6f4LVeylpK2Q7sqkiC8yWqQGihtw8J/yoyod12CbhwYfOQFytY7CENpCtQvmaTThw=="; x-amz-captcha-1=1462954478411556; x-amz-captcha-2=T6VRd5hpQ0PRa1ut01x7Kw==; csm-hit=s-0ZBGJ0SBMQ9BW3JSM2H8|1463111917503; ubid-main=188-1376416-9392823; session-id-time=2082787201l; session-id=190-0901353-9801359'
    }
    
    def __init__(self, url):
        self.base_url = "http://www.amazon.com"
        self.seen_urls = set()
        self.max_tasks = 50
        self.max_retry = 10
        self.loop = asyncio.get_event_loop()
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.q = Queue(loop = self.loop)
        
        self.manager = Manager()
        
        self.q.put_nowait(
            QueuingTask(url, PageType.laptoplist_page, LaptopInfoItem())
        )
        
        """
        for debug
        """
        self.item_cnt = 0
        self.page_cnt = 0
        self.f = open("D:\\Acer", 'w')

                
    def close(self):
        self.session.close()
        self.f.close()
            
    def parse_laptoplist(self, text):

        self.page_cnt += 1
        print("PARSE PAGE NO."+str(self.page_cnt))
        tasks = self.manager.list()
        p = Process(target=PageParsers.parse_laptoplist, args=(tasks, text,))
        p.start()
        p.join()
        return tasks
        
    def parse_laptopitem(self, text, info_item):
        
        tasks = self.manager.list()
        res = self.manager.list()
         
        p = Process(target = PageParsers.parse_laptopitem, args = (tasks, res, text, info_item,))
        p.start()
        p.join()
        
        for item in res:
            self.item_cnt += 1
            self.f.write(str(self.item_cnt) + "#" + str(item) + "\n")
            self.f.flush()
            print("NO." + str(self.item_cnt) + " item")
        return tasks
    
    def parse_laptopcomments(self, text, info_item):

        tasks = self.manager.list()
        res = self.manager.list()
        p = Process(target = PageParsers.parse_laptopcomments, args = (tasks, res, text, info_item,))
        p.start()
        p.join()
        for item in res:
            self.item_cnt += 1
            self.f.write(str(self.item_cnt) + "#" + str(item) + "\n")
            self.f.flush()
            print("NO." + str(self.item_cnt) + " item")
        return tasks
       

    async def crawl(self):
        workers = [asyncio.Task(self.work(), loop=self.loop) for _ in range(self.max_tasks)]
        try:
            await self.q.join()
            for worker in workers:
                worker.cancel()
        except Exception as e:
            LOGGER.error('[in crawl] unexpected error with message: ', e)
            raise e 
            
    async def fetch(self, queuingTask):
        """
        unpack task tuple
        """
        url, page_type, info_item = queuingTask
        
        """
        try to establish connection
        """
        tries = 0
        while tries < self.max_retry:
            try:
                response = await self.session.get(url, headers = AsyncCrawler.REQUEST_HEADERS)
                break
            except aiohttp.ClientError:
                pass
            
            tries += 1
        else:
            LOGGER.warning("fail to connect to "+url)
            return 
          
        try: 
            text = await response.text()
        except:
            LOGGER.warning("fail to get page content from " + url)
        else:            
            """
            parse response
            """
            try:
                if page_type == PageType.laptoplist_page:
                    links = self.parse_laptoplist(text)    
                elif page_type == PageType.laptopitem_page:
                    links = self.parse_laptopitem(text, info_item)
                elif page_type == PageType.laptopcomment_page:
                    links = self.parse_laptopcomments(text, info_item)
            
                for link in links:
                    self.q.put_nowait(link)
            except Exception as e:
                print("parse error")
                print(e)
                raise
            finally:
                await response.release()
                
    async def work(self):
        try:
            while True:
                queuingTask = await self.q.get()
                await self.fetch(queuingTask)
                self.q.task_done()
        except asyncio.CancelledError:
            pass
            
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    crawler = AsyncCrawler("http://www.amazon.com/s/ref=s9_acss_bw_cg_lgopc_2b1?node=13896617011&brand=Dell&lo=computers&pf_rd_m=ATVPDKIKX0DER&pf_rd_s=unified-hybrid-12&pf_rd_r=1RW9GAG72X5T22DTE9XS&pf_rd_t=101&pf_rd_p=2475582802&pf_rd_i=13896617011")    

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
        #f.close()
        