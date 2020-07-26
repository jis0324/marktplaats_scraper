# from selenium import webdriver
import time
import random
import os
from bs4 import BeautifulSoup
import csv
import requests
import re

base_dir = os.path.dirname(os.path.abspath(__file__))

class Crawlsystem(object):
  def __init__(self):
    global base_dir
    self.proxy_list = list()
    self.get_proxy_list()
    self.page_source = ''
    self.url_list = list()

  def get_proxy_list(self):
    path = base_dir + "/proxies.txt"
    with open(path) as proxy_file:
      self.proxy_list = [row.rstrip('\n') for row in proxy_file]

  def get_random_proxy(self):
    random_idx = random.randint(0, len(self.proxy_list))
    proxy_ip = "http://" + self.proxy_list[random_idx]
    return proxy_ip

  def get_vehicle_data(self, vehicle_url):
    return_data = {
      'plat_num' : '',
      'title' : '',
      'price' : '',
      'img' : '',
      'usps_data' : '',
      'attr_data' : '',
      'seller_info' : ''
    }

    try:
      proxies = { 'http': self.get_random_proxy() } 
      print('Selected Proxies : ', proxies)

      r = requests.get(vehicle_url, proxies=proxies)
      text = r.text
      
      if text:
        ########################## convert string to DOM ########################
        soup = BeautifulSoup(text, 'lxml')
        
        # ########################## Get Main Container ########################
        main_containers = soup.find_all('section', class_='l-main-left')
        aside_containers = soup.find_all('aside', class_='l-side-right')
        
        if main_containers:
          for container in main_containers:
            ########################## Get Vehicle Text ########################
            vehicle_text = container.find('section', class_='listing')
            
            if vehicle_text:
              l_top_content = vehicle_text.find('section', class_='l-top-content')
              l_bottom_content = vehicle_text.find('section', class_='l-body-content')
              
              if l_top_content:
                ############## Get Title ###############
                title = l_top_content.find('h1', id="title")
                if title:
                  return_data['title'] = title.text.strip()

                ############# Get Price #############
                price = l_top_content.find(id="vip-ad-price-container")
                if price:
                  return_data['price'] = price.text.strip()

                ############## Get Img ###############
                img = l_top_content.find(id="vip-gallery-thumbs").find('img')['src']
                if img:
                  return_data['img'] = img.strip()

                ############## Get USPs Data ##############
                usps_block_list = l_top_content.find(id="usps-block-container").find_all('div', class_='usp-block')
                usps_data_dict = dict()
                if usps_block_list:
                  for item in usps_block_list:
                    key = item.find('div', class_="usp-block-title").text.strip()
                    val = item.find('div', class_="usp-block-value").text.strip()
                    usps_data_dict[key] = val
                
                  return_data['usps_data'] = usps_data_dict
            
              if l_bottom_content:
                ############## Get Plat Number #############
                vehicle_attr_container = l_bottom_content.find(id="car-attributes").find('div', class_='car-feature-table')
                if vehicle_attr_container:
                  vehicle_attr_list = vehicle_attr_container.find_all('div', class_='spec-table-item')
                  if vehicle_attr_list:
                    vehicle_attr_dict = dict()
                    for item in vehicle_attr_list:
                      key = item.find('span', class_='key').text.strip()
                      val = item.find('span', class_='value').text.strip()
                      vehicle_attr_dict[key] = val

                    return_data['attr_data'] = vehicle_attr_dict

                    if 'Kenteken:' in vehicle_attr_dict:
                      return_data['plat_num'] = vehicle_attr_dict['Kenteken:']
                    elif 'Kenteken' in vehicle_attr_dict:
                      return_data['plat_num'] = vehicle_attr_dict['Kenteken']

        ############### Get Seller Info #############
        if aside_containers:
          for container in aside_containers:
            aside_text = container.find('section', class_='contact-info')
            if aside_text:
              aside_dict = dict()

              name = aside_text.find('h2', class_='name')
              if name:
                aside_dict['name'] = name.text.strip()
              
              vip_active_since = aside_text.find(id='vip-active-since')
              if vip_active_since:
                aside_dict['vip_active_since'] = re.sub(r'\s+', ' ', vip_active_since.text.strip())

              vip_seller_location = aside_text.find(id='vip-seller-location').find('h3')
              if vip_seller_location:
                aside_dict['vip_seller_location'] = vip_seller_location.text.strip()

              vip_seller_website = aside_text.find(id='vip-seller-website')
              if vip_seller_website:
                vip_seller_url = vip_seller_website.find(id='vip-seller-url')['data-url']
                if vip_seller_url:
                  aside_dict['vip_seller_website'] = vip_seller_url.strip()

              return_data['seller_info'] = aside_dict
              
        return return_data

    except Exception as err:
      print('Error In Vehicle Data : ', err)
      return return_data
      
  # def set_driver(self):
  #   random_proxy_ip = "http://" + self.get_random_proxy()        
  #   webdriver.DesiredCapabilities.CHROME['proxy'] = {
  #       "httpProxy":random_proxy_ip,
  #       "ftpProxy":random_proxy_ip,
  #       "sslProxy":random_proxy_ip,
  #       "proxyType":"MANUAL",
  #   }    
  #   user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) ' \
  #       'Chrome/80.0.3987.132 Safari/537.36'
  #   chrome_option = webdriver.ChromeOptions()
  #   chrome_option.add_argument('--no-sandbox')
  #   chrome_option.add_argument('--disable-dev-shm-usage')
  #   chrome_option.add_argument('--ignore-certificate-errors')
  #   chrome_option.add_argument("--disable-blink-features=AutomationControlled")
  #   chrome_option.add_argument(f'user-agent={user_agent}')
  #   chrome_option.headless = True
    
  #   driver = webdriver.Chrome('/usr/local/bin/chromedriver', options = chrome_option)
  #   return driver

  def main(self):

    file_eixits = os.path.isfile('vehicle_urls.csv')
    if file_eixits:
      with open('vehicle_urls.csv', 'r')  as urls_file:
        self.url_list = list(csv.reader(urls_file))
    
    print('Url List : ', len(self.url_list))

    for vehicle_url in self.url_list:
      try:
        vehicle_data = self.get_vehicle_data(vehicle_url[0])

        if vehicle_data:
          file_exists = os.path.isfile('vehicle_result.csv')
          with open( 'vehicle_result.csv', 'a', newline="", encoding='latin1', errors="ignore") as result_file:
            fieldnames = [ "plat_num", "title", "price", "img", "usps_data", "attr_data", "seller_info"]
            writer = csv.DictWriter(result_file, fieldnames=fieldnames)
            if not file_exists:
              writer.writeheader()
            writer.writerow(vehicle_data)
      except Exception as err:
        print('Error Write Data to CSV', err)
        continue
      
if __name__ == '__main__':
  crawlsystem = Crawlsystem()
  crawlsystem.main()