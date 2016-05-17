# AmazonCrawler

## Project Overview
### Reason for Starting this Project
>The reason I started this project is kind of stange: my laptop broke down! This reason seems have nothing to do with a web crawler. Please let me explain. 

>There is a serious problem with the screen of my laptop: whole screen is amost in red color and I can't see anything unless I use an external display. When I bought my laptop, I didn't pay too much attention to those comments on Internet about that model. I just didn't realize those information is very useful at that time. Now, my laptop broke down and I search that problem on Internet,  I frustratedly find that such problem is a common and unsolvable problem of that model. I am so regretted about I didn't check the comments on Internet when I decided to buy that model. 

>So, I think, if I gather the information of all the laptop models and their comments. Then, I can do something kinds of nature language processing on the comments(Honestly, I am totally not an expert of NLP. So, I am not sure which kind of technique should be used here. I am still working on that. Actually, the NLP part is beyond the scope of this project.). At least, I can extract some key words associated with positive/negative adjectives(In my case, that will be something like "screen"<-->"horrible".). This application may need significent mount of work at back end and front end to make it like a workable solution. Besides of that, the most important work is gathering the data. That's why I need to build a web crawler.  

### Original and Further Thoughts 
>The original object of this project is building a Python asynchronous web crawler with fixed parsing rules. At First, this crawler is built for crawling laptop informations on Amazon. Hence, the parsing rules for each page are designed only for certain kinds of pages and hard written as the member methods of crawler class with name parse_pagetype. This means that the code of this project can hardly be reused unless I am willing to refactor it.

>In the processing of development, I realized that the parsing rules could be seperated out, and common part of asynchronous IO, such as network IO, disk IO and etc, could be packed up and refactor as a frame work. There are surely some excellent scrawler frame works, like Scapy. But, I don't think all the affort I have spend on this project is meaningless.

## The Work Flow of AmazonCrawler
>In order to understand the work flow of this crawler, we must first under stand the date model. 
