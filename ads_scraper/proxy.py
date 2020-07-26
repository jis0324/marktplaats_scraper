import pymongo

# mongoclient = pymongo.MongoClient("mongodb+srv://Mycle:Piterpiter@cluster0-dqqoe.mongodb.net/test?retryWrites=true&w=majority")
mongoclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongoclient["mp_ads_scraper"]

collection = db['proxies']
proxy_list = [
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI991@196.240.249.71:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI992@196.240.249.72:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI993@196.240.249.74:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI994@196.240.249.95:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI995@196.240.249.103:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI996@196.240.249.133:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI997@196.240.249.143:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI998@196.240.249.152:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI999@196.240.249.157:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1000@196.240.249.158:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1001@196.240.249.160:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1002@196.240.249.232:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1003@196.240.249.250:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1004@196.245.165.54:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1005@196.245.165.56:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1006@196.245.165.58:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1007@196.245.165.60:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1008@196.245.165.62:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1009@196.245.165.63:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1010@196.245.165.81:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1011@196.245.165.86:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1012@196.245.165.87:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1013@196.245.165.89:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1014@196.245.165.90:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1015@196.245.165.92:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1016@196.245.165.94:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1017@196.245.165.96:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1018@196.245.165.97:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1019@196.245.165.99:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1020@196.245.165.100:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1021@196.245.165.130:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1022@196.245.165.136:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1023@196.245.165.137:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1024@196.245.165.150:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1025@196.245.165.165:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1026@196.245.165.187:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1027@196.245.165.197:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1028@196.245.165.209:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1029@196.245.165.217:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1030@196.245.165.226:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1031@196.245.165.230:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1032@196.245.165.231:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1033@196.245.165.233:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1034@196.245.165.236:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1035@196.245.165.237:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1036@196.245.165.238:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1037@196.245.165.245:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1038@196.245.165.250:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1039@196.245.165.251:13555",
  "celltrack:I6DHYNGIC9VVNMM4D4ZCI1040@196.245.165.252:13555",
]
for proxy in proxy_list:
  collection.insert_one({'proxy' : proxy})