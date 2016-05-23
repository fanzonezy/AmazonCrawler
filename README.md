# AmazonCrawler

## Project Overview
### Reason for Starting this Project
>The reason I started this project is kind of stange: my laptop broke down! This reason seems have nothing to do with a web crawler. Please let me explain. 

>There is a serious problem with the screen of my laptop: whole screen is amost in red color and I can't see anything unless I use an external display. When I bought my laptop, I didn't pay too much attention to those comments on Internet about that model. I just didn't realize those information is very useful at that time. Now, my laptop broke down and I search that problem on Internet,  I frustratedly find that such problem is a common and unsolvable problem of that model. I am so regretted about I didn't check the comments on Internet when I decided to buy that model. 

>So, I think, if I gather the information of all the laptop models and their comments. Then, I can do something kinds of nature language processing on the comments(Honestly, I am totally not an expert of NLP. So, I am not sure which kind of technique should be used here. I am still working on that. Actually, the NLP part is beyond the scope of this project.). At least, I can extract some key words associated with positive/negative adjectives(In my case, that will be something like "screen"<-->"horrible".). This application may need significent mount of work at back end and front end to make it like a workable solution. Besides of that, the most important work is gathering the data. That's why I need to build a web crawler.  

### Original and Further Thoughts 
>The original object of this project is building a Python asynchronous web crawler with fixed parsing rules. At First, this crawler is built for crawling laptop informations on Amazon. Hence, the parsing rules for each page are designed only for certain kinds of pages and hard written as the member methods of crawler class with name parse_pagetype. This means that the code of this project can hardly be reused unless I am willing to refactor it.

>In the processing of development, I realized that the parsing rules could be seperated out, and common part of asynchronous I/O, such as network I/O, disk I/O and etc, could be packed up and refactor as a frame work. There are surely some excellent scrawler frame works, like Scapy. But, I don't think all the affort I have spend on this project is meaningless.

## The Work Flow of AmazonCrawler
>In order to understand the work flow of this crawler, we must first under stand the data model.

>Generally, we can view the crawler as factory: In this factory, there is one pipline, products will be put into the pipline by a certain kind of worker, generator, that only GENERATE partially finished products. There is another kind of worker, appender, work on this pipline. They will take a partailly finished product and APPEND something to that product. After they finish their work, they will either put the product back to the pipline if that product still needs some work to be done or finished that product and put that product into back store.

>This is the general idea of this crawler framework(2016/5/22, at this point, I've only finshed the very basic structure of the framework.), Here comes the question how user use this frame work? Lets first use a general example to illustrate the usage, then we will fully analyze the exmple of crawling all the information of Laptops on Amazon.

>Before building a crawler by this framework, user must first has their data model in their mind and how the data can be obtained. If all the needed pages form a tree structure and requires a certain traversal strategies, this framework will be a quite suitable solution. Let imagine such a situation: I like a girl and I've added her as my friend on a forum. So, I can access her profile page, , and on her profile page I can find her favorite topics. By those topic links, I can access the main pages of those topics. Here is the problem: I want to receive push notifications of the 10th newest posts on my girl's favorite topics every day(If I read those post, I will have a lot stuff to talk with her), but the forum doesn't provide such a highly customized service. So, I have to build one on my own and the first thing to do is to build a crawler which can get me those posts, and then I can easily build a tiny Web service to send those posts either to my mailbox or my cell-phone.
>






