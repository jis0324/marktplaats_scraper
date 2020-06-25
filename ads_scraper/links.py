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

#mongoclient = pymongo.MongoClient("mongodb+srv://Mycle:Piterpiter@cluster0-dqqoe.mongodb.net/test?retryWrites=true&w=majority")
# mongoclient = pymongo.MongoClient("mongodb+srv://LiSun:akfdj0603@cluster0-uioxu.mongodb.net/marktplaats?retryWrites=true&w=majority")
mongoclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongoclient["mp_ads_scraper"]

reget_category_flag = False
base_dir = os.path.dirname(os.path.abspath(__file__))
category_list = [
  "ANTIEK_EN_KUNST",        #30137
  "AUDIO_TV_EN_FOTO",       #37653
  "AUTO_ONDERDELEN",        #8000
  "AUTO_DIVERSEN",          #7881
  "CD'S_EN_DVD'S",          #7831
  "COMPUTERS_EN_SOFTWARE",  #7614
  "BOEKEN",                 #7526
  "HUIS_EN_INRICHTING",     #7215
  "KINDEREN_EN_BABY'S",     #7190
  "KLEDING_DAMES",          #7092
  "FIETSEN_EN_BROMMERS",    #7013
  "SIERADEN_EN_TASSEN",     #7005
  "DOE_HET_ZELF_EN_VERBOUW",#6928
  "KLEDING_HEREN",          #6460
  "MUZIEK_EN_INSTRUMENTEN", #6123
  "SPORT_EN_FITNESS",       #6016
  "SPELCOMPUTERS_GAMES",    #5945
  "WITGOED_EN_APPARATUUR",  #6208
  "TUIN_EN_TERRAS",         #6184
  "HOBBY_EN_VRIJE_TIJD",    #5884
  "TELECOMMUNICATIE",       #5856
  "CARAVANS_EN_KAMPEREN",   #5835
  "DIVERSEN",               #5458
  "HUIZEN_EN_KAMERS",       #5438
  "DIEREN_EN_TOEBEHOREN",   #5248
  "ZAKELIJKE_GOEDEREN",     #5114
  "POSTZEGELS_EN_MUNTEN",   #5053
  "MOTOREN",                #4953
  "VERZAMELEN",             #4896
  "WATERSPORT_EN_BOTEN",    #4431
  "VAKANTIE",               #2290
  "TICKETS_EN_KAARTJES",    #2035
  "DIENSTEN_EN_VAKMENSEN",  #1942
  "VACATURES",              #883
  "CONTACTEN_EN_BERICHTEN", #198
]

class Crawlsystem(object):
  # initialize
  def __init__(self):
    global base_dir, reget_category_flag, db, category_list
    self.proxy_list = list()
    self.reget_category_flag = reget_category_flag
    self.db = db
    self.collection_cat_links = self.db['category_links']
    self.collection_detail_links = self.db['detail_links']
    self.get_proxy_list()
    self.category_list = category_list
    

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
        # print(err)
        continue

  # get category page
  # def get_category_page(self, category_name, category_url):
  def get_category_page(self):
    while True:
      if len(self.category_list) == 0:
        return

      category_name = self.category_list[0]
      del self.category_list[0]
      query = { 'name' : category_name }
      if self.collection_cat_links.count_documents(query):
        category_url = self.collection_cat_links.find_one(query)['link']
        
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
          if end_flag > 3:
            break
          
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

                driver.execute_script("window.scrollTo(0, " + str(scroll_height) + ");")
                time.sleep(delay_time)

              if end_flag > 3:
                driver.quit()
                print('----- Quit Chrome Driver For', category_name,'Categroy -----')
                break

            except Exception as err:
              # print('----- Error For', category_name, '-----')
              # print(err)
              continue

      else:
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
      # subprocess.Popen("python " + base_dir + "/link_scrapers/ANTIEK_EN_KUNST.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/AUDIO_TV_EN_FOTO.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/AUTO_ONDERDELEN.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/AUTO_DIVERSEN.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/BOEKEN.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/CARAVANS_EN_KAMPEREN.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/CD'S_EN_DVD'S.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/COMPUTERS_EN_SOFTWARE.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/CONTACTEN_EN_BERICHTEN.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/DIENSTEN_EN_VAKMENSEN.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/DIEREN_EN_TOEBEHOREN.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/DOE_HET_ZELF_EN_VERBOUW.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/FIETSEN_EN_BROMMERS.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/HOBBY_EN_VRIJE_TIJD.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/HUIS_EN_INRICHTING.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/HUIZEN_EN_KAMERS.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/KINDEREN_EN_BABY'S.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/KLEDING_DAMES.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/KLEDING_HEREN.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/MOTOREN.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/MUZIEK_EN_INSTRUMENTEN.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/POSTZEGELS_EN_MUNTEN.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/SIERADEN_EN_TASSEN.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/SPELCOMPUTERS_GAMES.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/SPORT_EN_FITNESS.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/TELECOMMUNICATIE.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/TICKETS_EN_KAARTJES.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/TUIN_EN_TERRAS.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/VACATURES.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/VAKANTIE.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/VERZAMELEN.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/WATERSPORT_EN_BOTEN.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/WITGOED_EN_APPARATUUR.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/ZAKELIJKE_GOEDEREN.py", shell=True, universal_newlines=True)
      # time.sleep(5)
      # subprocess.Popen("python " + base_dir + "/link_scrapers/DIVERSEN.py", shell=True, universal_newlines=True)

      if self.reget_category_flag:
        self.get_category_urls()

      # collist = self.db.list_collection_names()
      # if "category_links" in collist:
      #   category_list = self.collection_cat_links.find()
      #   print('----- Found', self.collection_cat_links.count_documents({}), 'Categories -----')
      #   for category in category_list:
      #     x = threading.Thread(target=self.get_category_page, args=( category['name'], category['link']))
      #     x.start()
      #     time.sleep(5)

      for x in range(10):
        thread = threading.Thread(target=self.get_category_page)
        thread.start()
        time.sleep(2)

    except Exception as err:
      # print('----- Error in Main Func -----')
      # print(err)
      return

if __name__ == '__main__':
  crawlsystem = Crawlsystem()
  crawlsystem.main()