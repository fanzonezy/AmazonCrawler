import asyncio
import aiohttp
#import objgraph
import sys
import re
import logging

from multiprocessing import Process, Manager
from AsyncCrawlerUtils import ParserType, QueuingTask, CrawlerMetaClass

try:
    from asyncio import JoinableQueue as Queue
except ImportError:
    from asyncio import Queue

LOGGER = logging.getLogger(__name__)
item_cnt = 0
              
class BaseAsyncCrawler(metaclass=CrawlerMetaClass):
    
    REQUEST_HEADERS = {
        'Host': "www.amazon.com",
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Cookie': 'p90x-info=AFF; x-wl-uid=1kb5U5f5c4rHaG4vz5zIWJu/tVAITMao2+trg9pgrg2fTKafMpUBUPkUqOuAjAIDQar3g8DV8B93eymfW+V36W9Jvd3BZaD+VnsW6BE6SBzwm+DvlwkMoQNBUTu2uqsvrf2Fq+4dOFPU=; session-token="3lAwr9G8TrLsJQD1W/uJPnaHRzyCKNO9Z2BPuj8VV3R6sBSx2+rux3gFClgxJRlut2Sh/P/BtwmpfCKlNPy00879qZbyLITRNtUvaAktIiY86+AOyco9bxIHOfDdsd4uNeNhKAEOqHAAZyJNxZpHI6f4LVeylpK2Q7sqkiC8yWqQGihtw8J/yoyod12CbhwYfOQFytY7CENpCtQvmaTThw=="; x-amz-captcha-1=1462954478411556; x-amz-captcha-2=T6VRd5hpQ0PRa1ut01x7Kw==; csm-hit=s-0ZBGJ0SBMQ9BW3JSM2H8|1463111917503; ubid-main=188-1376416-9392823; session-id-time=2082787201l; session-id=190-0901353-9801359'
    }
    
    def __init__(self, task):
        self.seen_url = set()
        self.max_tasks = 50
        self.max_retry = 10
        self.loop = asyncio.get_event_loop()
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.q = Queue(loop = self.loop)
        
        self.manager = Manager()
        
        self.q.put_nowait(task)
        
        """
        for debug
        """
        self.item_cnt = 0
        self.page_cnt = 0
        self.f = open("D:\\Acer", 'w')
        print('initialization finished.')
                
    def close(self):
        self.session.close()
        self.f.close()
        
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
        print('fetching')
    
        """
        unpack task tuple
        """
        url, page_type, info_item = queuingTask
        print(url)
        """
        try to establish connection
        """
        tries = 0
        while tries < self.max_retry:
            try:
                response = await self.session.get(url, headers = BaseAsyncCrawler.REQUEST_HEADERS)
                break
            except aiohttp.ClientError:
                pass
            
            tries += 1
        else:
            LOGGER.warning("fail to connect to "+url)
            return 
          
        print('connection established.')
        try: 
            text = await response.text()
        except:
            print("fail to get page content from " + url)
        else:            
            """
            parse response
            """
            try:
                
                todo = self.manager.list()
                done = self.manager.list()
                
                print(self.__dict__)
                print(hasattr(self, '__mapping__'))
                
                if hasattr(self, '__mapping__'):
                    print("+++")
                    parser = self.__mapping__[page_type]
                    print("---")
                    #import pickle
                    #pickle.dumps(parser)
                    print('parsing '+page_type)
                    if parser.parser_type == ParserType.GENERATOR:
                        p = Process(target=parser, args=(todo, done, text,))
                    elif parser.parser_type == ParserType.APPENDER:
                        p = Process(target=parser, args=(todo, done, text, info_item,))
                    else:
                        raise Exception('fatal: unrecognized parser type')
                    
                    p.start()
                    p.join()
                    
                    for task in todo:
                        self.q.put_nowait(task)
                    
                    for data_item in done:   
                        self.item_cnt += 1
                        self.f.write(str(self.item_cnt) + "#" + str(data_item) + "\n")
                        self.f.flush()
                        print("NO." + str(self.item_cnt) + " item")   
                    
                else:
                    raise Exception('fatal: uninitialized crawler.')
            except Exception as e:
                print(e)
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
            

        