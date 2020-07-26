from selenium import webdriver
import time
import random
import os
from bs4 import BeautifulSoup
import csv

base_dir = os.path.dirname(os.path.abspath(__file__))

class Crawlsystem(object):
  def __init__(self):
    global base_dir
    self.proxy_list = list()
    self.get_proxy_list()
    self.page_source = ''

  def get_proxy_list(self):
    path = base_dir + "/proxies.txt"
    with open(path) as proxy_file:
      self.proxy_list = [row.rstrip('\n') for row in proxy_file]

  def get_random_proxy(self):
    random_idx = random.randint(0, len(self.proxy_list))
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
    
    driver = webdriver.Chrome('/usr/local/bin/chromedriver', options = chrome_option)
    return driver

  def get_vehicle_url(self):
    ########################## convert string to DOM ########################
    soup = BeautifulSoup(self.page_source, 'lxml')

    ########################## get feed-items-container ########################
    feed_containers = soup.find_all('div', class_='feed-items-container')

    for feed_container in feed_containers:
      ########################## get all vehicles ########################
      vehicles = feed_container.find_all('article', class_='feed-item')
      for vehicle in vehicles:
        ########################## get vehicle url ########################
        vehicle_url = vehicle.find('a')['href']

        with open(base_dir + '/vehicle_urls.csv', 'a', newline="" ) as url_file:
          writer = csv.writer(url_file)
          writer.writerow([vehicle_url])
      

  def main(self):
    self.driver = self.set_driver()
    print('----- Created Chrome Driver -----')
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
    # with open(base_dir + '/result_before.txt', 'w', encoding='latin1', errors='ignore') as result_file:
    #   result_file.write(self.page_source)

    ########################## get current page height ########################
    before_height = self.driver.execute_script("return document.body.scrollHeight")
    delay_time = 1
    while True:
      scroll_height = before_height - 2500
      while True:
        try:
          scroll_height = scroll_height - 200
          current_height = self.driver.execute_script("return document.body.scrollHeight")
          delay_time = int(current_height / 10000)
          ########################## if page source height increased ########################
          if current_height > before_height:
            print( 'before_height : ', before_height, 'current height : ', current_height)
            self.page_source = self.driver.page_source
            self.get_vehicle_url()
            before_height = current_height
            # with open(base_dir + '/result_after.txt', 'w', encoding='latin1', errors='ignore') as result_file:
            #   result_file.write(page_source)

            break
          ########################## if page source height not changed ########################
          else:
            print('scroll down : ', str(scroll_height))

            if scroll_height < 0:
              scroll_height = current_height

            self.driver.execute_script("window.scrollTo(0, " + str(scroll_height) + ");")
            time.sleep(delay_time)
        except Exception as err:
          print('*********** Error ***********', err)
          continue

    # if self.after_height > self.before_height:
    #   page_source = self.driver.page_source


    


if __name__ == '__main__':
  crawlsystem = Crawlsystem()
  crawlsystem.main()