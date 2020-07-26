import pymongo

mongoclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongoclient["mp_car_scraper"]
collection = db['proxies']
proxy_list = list()

with open('proxies.txt', 'r', encoding="latin1", errors="ignore") as proxies_file:
  proxies = proxies_file.read()
  proxy_list = proxies.split('\n')

for proxy in proxy_list:
  if collection.count_documents({'proxy' : proxy}) > 0:
    print('Duplicated proxy!')
  else:
    collection.insert_one({'proxy' : proxy})
