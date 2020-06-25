from selenium import webdriver
import time
import random
import os
from bs4 import BeautifulSoup
import pymongo
from datetime import datetime

# global variables
base_dir = os.path.dirname(os.path.abspath(__file__))
reget_category_flag = True
# mongodb setting
# mongoclient = pymongo.MongoClient("mongodb+srv://Mycle:Piterpiter@cluster0-dqqoe.mongodb.net/test?retryWrites=true&w=majority")
mongoclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongoclient["mp_car_scraper"]

class Crawlsystem(object):
  def __init__(self):
    global base_dir, reget_category_flag, db
    self.proxy_list = list()
    self.get_proxy_list()
    self.reget_category_flag = reget_category_flag
    self.db = db

  def get_proxy_list(self):
    collection = db['proxies']
    proxy_list = collection.find()
    for proxy in proxy_list:
      self.proxy_list.append(proxy['proxy'])

  def get_random_proxy(self):
    random_idx = random.randint(0, len(self.proxy_list)-1)
    proxy_ip = self.proxy_list[random_idx]
    return proxy_ip

  def set_driver(self):
    random_proxy_ip = "http://" + self.get_random_proxy()        
    webdriver.DesiredCapabilities.CHROME['proxy'] = {
        "httpProxy":random_proxy_ip,
        "ftpProxy":random_proxy_ip,
        "sslProxy":random_proxy_ip,
        "proxyType":"MANUAL",
    }    
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) ' \
        'Chrome/80.0.3987.132 Safari/537.36'
    chrome_option = webdriver.ChromeOptions()
    chrome_option.add_argument('--no-sandbox')
    chrome_option.add_argument('--disable-dev-shm-usage')
    chrome_option.add_argument('--ignore-certificate-errors')
    chrome_option.add_argument("--disable-blink-features=AutomationControlled")
    chrome_option.add_argument(f'user-agent={user_agent}')
    chrome_option.headless = True
    
    driver = webdriver.Chrome(options = chrome_option)
    # driver = webdriver.Chrome('/usr/local/bin/chromedriver', options = chrome_option)
    return driver

  def get_vehicle_url(self):
    # use db
    collection = self.db['links']
    ########################## convert string to DOM ########################
    soup = BeautifulSoup(self.page_source, 'lxml')

    ########################## get feed-items-container ########################
    feed_containers = soup.find_all('div', class_='feed-items-container')

    for feed_container in feed_containers:
      ########################## get all vehicles ########################
      vehicles = feed_container.find_all('article', class_='feed-item')
      for vehicle in vehicles:
        ########################## get vehicle url ########################
        temp_data = {}
        vehicle_url = vehicle.find('a')['href'].strip()
        temp_data["link"] = vehicle_url
        now = datetime.now()
        temp_data['dtime'] = now.strftime("%d-%m-%Y %H:%M")
        # insert data to collection
        if collection.count_documents({'link':temp_data['link']}) == 0:
          collection.insert_one(temp_data)
    
    print('URL Count : ', collection.count_documents({}))

  def main(self):
    
    self.driver = self.set_driver()
    # print('----- Created Chrome Driver -----')
    self.driver.get("https://www.marktplaats.nl/c/auto-s/c91.html")
    
    ########################## click more button ########################
    more_btns = self.driver.find_elements_by_css_selector("div.l1-category-feed-container div.show-more-feed-link span.mp-Button")

    for item in more_btns:
      if item.is_displayed():
          self.driver.execute_script("arguments[0].click();", item)
          time.sleep(1)
    
    ########################## get current page source ########################
    self.page_source = self.driver.page_source
    self.get_vehicle_url()

    ########################## get current page height ########################
    before_height = self.driver.execute_script("return document.body.scrollHeight")
    delay_time = 1
    while True:
      scroll_height = before_height - 2500
      while True:
        try:
          scroll_height = scroll_height - 200
          current_height = self.driver.execute_script("return document.body.scrollHeight")
          delay_time = 1 + int(current_height / 100000)
          ########################## if page source height increased ########################
          if current_height > before_height:
            # print( 'before_height : ', before_height, 'current height : ', current_height)
            self.page_source = self.driver.page_source
            self.get_vehicle_url()
            before_height = current_height
            break
          ########################## if page source height not changed ########################
          else:
            # print('scroll down : ', str(scroll_height))

            if scroll_height < (current_height - 10000) or scroll_height < 0:
              scroll_height = current_height

            self.driver.execute_script("window.scrollTo(0, " + str(scroll_height) + ");")
            time.sleep(delay_time)
        except Exception as err:
          print('*********** Error ***********', err)
          continue

if __name__ == '__main__':
  crawlsystem = Crawlsystem()
  crawlsystem.main()