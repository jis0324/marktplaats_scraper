import pymongo

# mongoclient = pymongo.MongoClient("mongodb+srv://Mycle:Piterpiter@cluster0-dqqoe.mongodb.net/test?retryWrites=true&w=majority")
mongoclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongoclient["mp_ads_scraper"]

collection = db['proxies']
proxy_list = [
  #***
]
for proxy in proxy_list:
  collection.insert_one({'proxy' : proxy})
