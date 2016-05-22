from enum import Enum
from collections import namedtuple
from functools import wraps

QueuingTask = namedtuple('QueuingTask', ['url', 'page_type', 'info_item'])

class ParserType(Enum):
    GENERATOR = 'GENERATOR'
    APPENDER = 'APPENDER'
    
"""
This is a decorator to mark a method as a parser 
of a certain kind of page indicated by 'page_type'
parameter.

NOTE: pickle library doesn't support function decorator, 
So, here is necessary to use such a sort of ugly
'class' decorator to bypass that limitation. 
"""
class parsermethod(object):
    def __init__(self, parser_type, page_type):
        self.parser_type = parser_type
        self.page_type = page_type


    def __call__(self, func):
    
        if not isinstance(self.parser_type, ParserType):
            raise Exception('fatal: the type of a parser must be ParserType.')
    
        if not isinstance(self.page_type, str):
            raise Exception('fatal: the type of a page must be string type') 
     
        #@wraps(func)
        def wrapped(task_queue, shared_list, *args, **kwargs):
            todo, done = func(*args, **kwargs)
            
            for task in todo:
                task_queue.put(task)
            for data_item in done:
                shared_list.append(data_item) 
                
        wrapped.__setattr__('page_type', self.page_type)
        wrapped.__setattr__('parser_type', self.parser_type)
        return wrapped

"""
This is the metaclass for any parser collection 
classes. This metaclass will collect all the decorated 
parser methods and associate each parse with the 
name of a page type. These mappings are stored in 
a special variable '__mapping__'.
"""    
class CrawlerMetaClass(type):
    def __new__(cls, name, bases, attrs):
        if name == 'BaseAsycCrawler':
            return super().__new__(cls, name, bases, attrs)
        
        mapping = {}
        to_delete = []
        for k, v in attrs.items():
            if hasattr(attrs[k], 'page_type'):
                mapping[attrs[k].page_type] = v
                to_delete.append(k)
                
        for k in to_delete:
            if hasattr(attrs[k], 'page_type'):
                attrs.pop(k)
                
        attrs['__mapping__'] = mapping
        return super().__new__(cls, name, bases, attrs)
                       

