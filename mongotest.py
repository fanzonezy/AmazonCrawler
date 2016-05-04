#!/usr/bin/env python

from pymongo import *

client = MongoClient('localhost', 27017)

db = client.test
col = db.test_collection
post = {
	"author": "sb",
	"tag": ['sb', 'zz']
}

print(col.insert_one(post).inserted_id)
print(col.find().pretty())


