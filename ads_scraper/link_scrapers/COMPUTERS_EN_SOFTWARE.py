from selenium import webdriver
import time
import random
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup
import pymongo
import requests
import threading
import subprocess

reget_category_flag = False

base_dir = os.path.dirname(os.path.abspath(__file__))

#mongoclient = pymongo.MongoClient("mongodb+srv://Mycle:Piterpiter@cluster0-dqqoe.mongodb.net/test?retryWrites=true&w=majority")
# mongoclient = pymongo.MongoClient("mongodb+srv://LiSun:akfdj0603@cluster0-uioxu.mongodb.net/marktplaats?retryWrites=true&w=majority")
mongoclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongoclient["mp_ads_scraper"]

class Crawlsystem(object):
  # initialize
  def __init__(self):
    global base_dir, reget_category_flag, db
    self.proxy_list = list()
    self.reget_category_flag = reget_category_flag
    self.db = db
    self.collection_cat_links = self.db['category_links']
    self.collection_detail_links = self.db['detail_links']
    self.get_proxy_list()

  # get proxy list  
  def get_proxy_list(self):
    collection = self.db['proxies']
    proxy_list = collection.find()
    for proxy in proxy_list:
      self.proxy_list.append(proxy['proxy'])

  # get a random proxy
  def get_random_proxy(self):
    random_idx = random.randint(0, len(self.proxy_list)-1)
    proxy_ip = self.proxy_list[random_idx]
    return proxy_ip

  # create chrome driver
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

  # get category urls
  def get_category_urls(self):
    proxies = { 'http': self.get_random_proxy() } 
    print('Selected Proxies : ', proxies)

    while True:
      try:
        r = requests.get('https://www.marktplaats.nl/', proxies=proxies)
        page_source = r.text
        
        if page_source != '':
          ########################## convert string to DOM ########################
          soup = BeautifulSoup(page_source, 'lxml')
          category_container = soup.find(id='navigation-categories')
          if category_container:
            category_items = category_container.find_all('li', class_="link")
            for item in category_items:
              temp_dict = dict()
              temp_dict['name'] = re.sub(r'\s+|\-', '_', re.sub(r'\,|\|', '', item.find('a').text.strip().upper()))
              temp_dict['link'] = item.find('a')['href'].strip()
              temp_dict['date'] = str(datetime.today())

              if temp_dict['link'] == 'https://www.marktplaats.nl/c/auto-s/c91.html':
                continue
              
              if self.collection_cat_links.count_documents({'link':temp_dict['link']}) == 0:
                self.collection_cat_links.insert_one(temp_dict)
            return
      except Exception as err:
        print(err)
        continue

  # get category page
  def get_category_page(self, category_name, category_url):
    driver = self.set_driver()
    print('----- Created Chrome Driver For', category_name,'Categroy -----')

    driver.get(category_url)

    ########################## delete existing collection ########################
    # collist = self.db.list_collection_names()
    # if category_name + '_LINKS' in collist:
    #   self.db[category_name + '_LINKS'].drop()
    
    ########################## click more button ########################
    more_btns = driver.find_elements_by_css_selector("div.l1-category-feed-container div.show-more-feed-link span.mp-Button")
    if more_btns:
      for more_btn in more_btns:
        if more_btn.is_displayed():
          driver.execute_script("arguments[0].click();", more_btn)
          print('----- Clicked More Btn For', category_name, 'Category -----')
          time.sleep(1)

    ########################## get current page source ########################
    page_source = driver.page_source
    
    ########################## get detail urls ########################
    self.get_detail_url(category_name, page_source)

    # ########################## get current page height ########################
    before_height = driver.execute_script("return document.body.scrollHeight")    
    end_flag = 0
    while True:
      scroll_height = before_height - 1500
      end_flag = 0
      while True:
        try:
          scroll_height = scroll_height - 200
          current_height = driver.execute_script("return document.body.scrollHeight")
          delay_time = 1 + int(current_height/100000)

          ########################## if page source height increased ########################
          if current_height > before_height:
            # print( 'before_height : ', before_height, 'current_height : ', current_height)
            page_source = driver.page_source
            self.get_detail_url(category_name, page_source)
            before_height = current_height
            break
          ########################## if page source height not changed ########################
          else:
            if scroll_height < (current_height - 10000) or scroll_height < 0:
              end_flag += 1
              scroll_height = current_height

            # print('scroll down : ', str(scroll_height))
            driver.execute_script("window.scrollTo(0, " + str(scroll_height) + ");")
            time.sleep(delay_time)

          if end_flag > 3:
            driver.quit()
            print('----- Quit Chrome Driver For', category_name,'Categroy -----')

        except Exception as err:
          print('----- Error For', category_name, '-----')
          print(err)
          continue

  # get catagory detail urls
  def get_detail_url(self, category_name, page_source):

    ########################## convert string to DOM ########################
    soup = BeautifulSoup(page_source, 'lxml')
    
    ########################## get feed-items-container ########################
    feed_containers = soup.find_all('div', class_='feed-items-container')
    
    if feed_containers:
      for feed_container in feed_containers:
        ########################## get all vehicles ########################
        details = feed_container.find_all('article', class_='feed-item')

        for detail in details:
          ########################## get vehicle url ########################
          temp_data = {}
          detail_url = detail.find('a')['href'].strip()
          if detail_url:
            temp_data["link"] = detail_url
            temp_data['ad_category'] = category_name
            now = datetime.now()
            temp_data['dtime'] = now.strftime("%d-%m-%Y %H:%M")

            # insert data to collection
            if self.collection_detail_links.count_documents({'link':detail_url}) == 0:
              self.collection_detail_links.insert_one(temp_data)
      print('------------------------------------------------------')
      print(category_name, 'category detail url number : ', self.collection_detail_links.count_documents({'ad_category':category_name}))

  # main function
  def main(self):

    try:
      self.get_category_page('COMPUTERS_EN_SOFTWARE', 'https://www.marktplaats.nl/c/computers-en-software/c322.html')
      # if self.reget_category_flag:
      #   self.get_category_urls()

      # collist = self.db.list_collection_names()
      # if "category_links" in collist:
      #   category_list = self.collection_cat_links.find()
      #   print('----- Found', self.collection_cat_links.count_documents({}), 'Categories -----')
      #   for category in category_list:
      #     output = subprocess.Popen("python " + base_dir + "/link_scrapers/"+ category['name'] +".py", shell=True, universal_newlines=True)
      #     x = threading.Thread(target=self.get_category_page, args=( category['name'], category['link']))
      #     x.start()
      #     time.sleep(5)

    except Exception as err:
      print('----- Error in Main Func -----')
      print(err)

if __name__ == '__main__':
  crawlsystem = Crawlsystem()
  crawlsystem.main()