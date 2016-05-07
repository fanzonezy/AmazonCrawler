import asyncio
import aiohttp
import resource
import re 
from AmazonLaptopCommons import PageType, selectorOf, LaptopInfoItem, CommentItem, QueuingTask
from bs4 import BeautifulSoup


try:
    from asyncio import JoinableQueue as Queue
except ImportError:
    from asyncio import Queue
    
class AsyncCrawler(object):
    
    REQUEST_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/ 39.0.2171.95 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'en-US,en;q=0.8'
    }
    
    def __init__(self, url):
        self.base_url = "http://www.amazon.com"
        self.seen_urls = set()
        self.max_tasks = 50
        self.max_retry = 10
        self.loop = asyncio.get_event_loop()
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.q = Queue(loop = self.loop)
        
        self.q.put_nowait(
            QueuingTask(url, PageType.laptoplist_page, None)
        )
        
        """
        for debug
        """
        self.item_cnt = 0
        self.page_cnt = 0
        
        print()
        
    def close(self):
        self.session.close()
        
    @asyncio.coroutine
    def parse_laptoplist(self, response):
        """
        TODO:
        (1) parse all the links to laptop items(add to queue).
        (2) parse one link to next laptop list page(add to queue).
        """
        self.page_cnt += 1
        print("PARSE PAGE NO."+str(self.page_cnt))
        
        tasks = set()
        #body = yield from response.read()
        
        try:
            text = yield from response.text()
        except:
            print("PAGE " + str(self.page_cnt) + " WENT WRONG.")
            raise
        
        #print(text)
        soup = BeautifulSoup(text, 'html.parser')
        #items = soup.select(selectorOf['all_laptop_items'])
        items = [item.find('a') for item in soup.find_all("li", id = re.compile("^result_"))]
                
        """
        add item links
        """
        print(len(items))
        for item in items:
            url = item['href']
            print(url)
            info_item = LaptopInfoItem()
            info_item.asin = re.findall(r'\/B[0-9A-Z]{9}\/', url)[0][1:-1]
            #print("ADD " + info_item.asin + "INTO QUEUE")
            tasks.add(
                QueuingTask(url, PageType.laptopitem_page, info_item)
            )
            
        """
        add next page link
        """
        try:
            next_page_url = soup.select(selectorOf['next_page_link'])[0]['href']
            tasks.add(
                QueuingTask(self.base_url+next_page_url, PageType.laptoplist_page, None)
            )
        except:
            print('CAN NOT REACH NEXT PAGE')
        
        return tasks
    
    @asyncio.coroutine
    def parse_laptopitem(self, response, info_item):
        """
        TODO:
        (1) parse all the basic information about a laptop model:
            (a) asin serial number
            (b) model title
            (c) rating
            (d) price
            (e) brand
            ...
        (2) parse the link to comment list page(add to queue).
        """
        
        #info_item = LaptopInfoItem()
        
        tasks = set()
        
        try:
            text = yield from response.text()
        except Exception:
            print("WHEN PARSE LAPTOP: "+ info_item.asin + " WENT WRONG")
            print("SIZE OF QUEUE: " + str(self.q.qsize()))
            raise 
        
        soup = BeautifulSoup(text, 'html.parser')
        try:
            info_item.title = soup.select(selectorOf['product_title'])[0].string
            info_item.brand = soup.select(selectorOf['product_brand'])[0].string
            info_item.rating = soup.select(selectorOf['product_rating'])[0].string
            info_item.price = soup.select(selectorOf['product_price'])[0].string
        except:
            pass
        
        try:
            #go to comments page
            url = soup.select(selectorOf['comment_page_link'])[0]['href']
            tasks.add(
                QueuingTask(url, PageType.laptopcomment_page, info_item)
            )
        except:
            print("CANNOT REACH COMMENT PAGE for " + info_item.asin + ".")
            self.item_cnt += 1
            print("No." + str(self.item_cnt) + ":" + info_item.asin + " HAS FINISHED")
            pass
        
        return tasks
    
    def parse_laptopcomments(self, response, info_item):
        """
        TODO:
        (1) parse all the comments:
            (a) customer name
            (b) rating
            (c) comment title
            (d) comment body
        (2) parse the link to next comment list page(add to queue).
        """
        
        tasks = set()
        
        try:
            text = yield from response.text()
        except:
            print("WHEN PARSE COMMENTS OF "+info_item.asin + " WENT WRONG.")
            print("SIZE OF QUEUE: " + str(self.q.qsize()))
            raise
        soup = BeautifulSoup(text, 'html.parser')
        
        """
        parse all comments 
        """
        for cmmt_soup in soup.select(selectorOf['comment_item']):
            cmmt_item = CommentItem()
            try:
                cmmt_item.rating = cmmt_soup.select(selectorOf['product_rating_in_comment'])[0].string
                cmmt_item.customer_name = cmmt_soup.select(selectorOf['customer_name'])[0].string
                cmmt_item.comment_title = cmmt_soup.select(selectorOf['comment_title'])[0].string
                cmmt_item.comment_body = " ".join([s for s in cmmt_soup.select(selectorOf['comment_body'])[0].strings])
            except:
                print("ERROR WHEN PARSE " + info_item.asin + "'S COMMENT")
                pass
            else:
                info_item.comments.append(cmmt_item)
        try:
            next_page_url = soup.select(selectorOf['comment_next_page_link'])[0]['href']
            tasks.add(
                QueuingTask(self.base_url+next_page_url, PageType.laptopcomment_page, info_item)
            )
        except:
            self.item_cnt += 1
            print("No." + str(self.item_cnt) + ":" + info_item.asin + " HAS FINISHED")
        return tasks

    @asyncio.coroutine
    def crawl(self):
        workers = [asyncio.Task(self.work(), loop=self.loop) for _ in range(self.max_tasks)]
        yield from self.q.join()
        for worker in workers:
            worker.cancel()
        
    @asyncio.coroutine
    def fetch(self, queuingTask):
        """
        unpack task tuple
        """
        url, page_type, info_item = queuingTask
        #print("BEGIN TO FETCH: " + url)
        """
        try to establish connection
        """
        tries = 0
        while tries < self.max_retry:
            try:
                response = yield from self.session.get(url, headers = AsyncCrawler.REQUEST_HEADERS)
                break
            except aiohttp.ClientError:
                pass
            
            tries += 1
        else:
            print("FAIL TO CONNECT TO "+url)
            return 
        
        #print("CONNECTION ESTABLISHED")
        #print(response.headers)
        #text = yield from response.json()
        #print(text)
        """
        parse response
        """
        try:
            
            if page_type == PageType.laptoplist_page:
                links = yield from self.parse_laptoplist(response)
            elif page_type == PageType.laptopitem_page:
                links = yield from self.parse_laptopitem(response, info_item)
            elif page_type == PageType.laptopcomment_page:
                links = yield from self.parse_laptopcomments(response, info_item)
            
            for link in links:
                self.q.put_nowait(link)
            #for link in links.difference(self.seen_urls):
            #    self.q.put_nowait(link)
            #self.seen_urls.update(links)
        except:
            raise
        finally:
            yield from response.release()
    
    @asyncio.coroutine
    def work(self):
        try:
            while True:
                queuingTask = yield from self.q.get()
                yield from self.fetch(queuingTask)
                self.q.task_done()
        except asyncio.CancelledError:
            pass 
        
    def correct_url(self, url):
        return 
        
loop = asyncio.get_event_loop()
crawler = AsyncCrawler("http://www.amazon.com/s/ref=s9_acss_bw_bf_abcdefgh_1_img?rh=i%3Acomputers%2Cn%3A565108&field-availability=-1&field-brandtextbin=Acer&ie=UTF8&pf_rd_m=ATVPDKIKX0DER&pf_rd_s=merchandised-search-10&pf_rd_r=1VQZCF5T7GRS1QFW0TKG&pf_rd_t=101&pf_rd_p=2405855262&pf_rd_i=565108")    
try:
    loop.run_until_complete(crawler.crawl())  # Crawler gonna crawl.
except KeyboardInterrupt:
    #sys.stderr.flush()
    print('\nInterrupted\n')
finally:
    #reporting.report(crawler)
    crawler.close()

    # next two lines are required for actual aiohttp resource cleanup
    loop.stop()
    #loop.run_forever()

    loop.close()