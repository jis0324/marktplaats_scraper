from selenium import webdriver
import time
import random
import os
from bs4 import BeautifulSoup
import csv
import requests
import re
import pymongo
import json
import urllib.request
import uuid
from datetime import datetime

# global variables
base_dir = os.path.dirname(os.path.abspath(__file__))
reget_category_flag = True
# mongodb setting
mongoclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongoclient["mp_car_scraper"]

class Crawlsystem(object):

  def __init__(self):
    global base_dir, db
    self.proxy_list = list()
    self.get_proxy_list()
    self.url_list = list()
    self.db = db

  def get_proxy_list(self):
    collection = db['proxies']
    proxy_list = collection.find()
    for proxy in proxy_list:
      self.proxy_list.append(proxy['proxy'])

  def get_random_proxy(self):
    random_idx = random.randint(0, len(self.proxy_list)-1)
    proxy_ip = "http://" + self.proxy_list[random_idx]
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

  # get vehicle page source
  def get_vehicle_page(self, url):
    try:
      proxies = { 'http': self.get_random_proxy() }
      # print('Selected Proxies : ', proxies)
      r = requests.get(url, proxies=proxies)
      page_source = r.text

      # self.driver = self.set_driver()
      # print('----- Created Chrome Driver -----')
      # self.driver.get(url)

      # page_source = self.driver.page_source
      # self.driver.quit()

      return page_source
    except Exception as err:
      print(err)
      return ''

  # get header container info (title, view_count, favorited_count, displayed_since, price)
  def get_header_info(self, content):
    return_data = dict()

    if content:
      try:
        ############## Get Title ###############
        title = content.find(id="title")
        if title:
          return_data['ad_title'] = title.text.strip()
      except:
        pass

      try:
        ############## Get VIew Count ###############
        view_count = content.find(id="view-count")
        if view_count:
          return_data['view_count'] = view_count.text.strip()
      except:
        pass

      try:
        ############## Get Favorited Count ###############
        favorited_count = content.find(id="favorited-count")
        if favorited_count:
          return_data['fav_count'] = favorited_count.text.strip()
      except:
        pass

      try:
        ############## Get Displayed Since ###############
        displayed_since = content.find(id="displayed-since")
        if displayed_since:
          return_data['ad_online_date'] = re.sub(r'\s+', ' ', displayed_since.text.strip())
      except:
        pass

      try:
        ############## Get Price ###############
        price = content.find(id="vip-ad-price-container")
        if price:
          return_data['ad_price'] = price.text.strip()
      except:
        pass
      
    return return_data
    
  # get gallery container info ( img, mileage, construction_year, consumption_KM/L, energy_label, guarantee )
  def get_gallery_info(self, content):
    return_data = dict()
    
    if content:
      try:
        ############## Get Img ###############
        # img = content.find(id="vip-gallery-thumbs")
        # if img:
        #   return_data['img'] = img.find('img')['src'].strip()
        img_container = content.find(id="vip-carousel")
        if img_container:
          try:
            imgs_text = img_container['data-images-xxl']
            imgs = imgs_text.split('&')
            return_data['imgs'] = imgs[0:4]
          except:
            try:
              imgs_text = img_container['data-images-xl']
              imgs = imgs_text.split('&')
              return_data['imgs'] = imgs[0:4]
            except:
              try:
                imgs_text = img_container['data-images-l']
                imgs = imgs_text.split('&')
                return_data['imgs'] = imgs[0:4]
              except:
                try:
                  imgs_text = img_container['data-images-s']
                  imgs = imgs_text.split('&')
                  return_data['imgs'] = imgs[0:4]
                except:
                  pass
      except:
        pass
      
      try:
        ############## Get USPs Data ##############
        usps_block_list = content.find(id="usps-block-container").find_all('div', class_='usp-block')
        if usps_block_list:
          for item in usps_block_list:
            try:
              key = item.find('div', class_="usp-block-title").text.strip()
              val = item.find('div', class_="usp-block-value").text.strip()
              
              if 'stand' in key:
                return_data['mileage'] = re.sub(r'-', '', val)
              elif 'Bouwjaar' in key:
                return_data['construction_year'] = re.sub(r'-', '', val)
              elif 'Verbruik' in key:
                return_data['consumption'] = re.sub(r'-', '', val)
              elif 'Energielabel' in key:
                return_data['energy_label'] = re.sub(r'-', '', val)
              elif 'Garantie' in key:
                return_data['garantie'] = re.sub(r'-', '', val)
              else:
                return_data[key] = re.sub(r'-', '', val)
            except:
              continue

      except:
        pass
      
    return return_data

  # get vehicle attributes info ()
  def get_attr_info(self, content):
    return_data = dict()
    if content:
      try:
        vehicle_attr_container = content.find('div', class_='car-feature-table')
        if vehicle_attr_container:
          vehicle_attr_list = vehicle_attr_container.find_all('div', class_='spec-table-item')
          if vehicle_attr_list:
            for item in vehicle_attr_list:
              try:
                key = item.find('span', class_='key').text.strip()
                value = item.find('span', class_='value').text.strip()
                if key:
                  key = re.sub(r':', '', key).strip()
                  if key == 'Opties':
                    option_container = item.find('ul', class_='bulleted')
                    if option_container:
                      option_list = option_container.find_all('li')
                      options = list()
                      for option in option_list:
                        options.append(option.text.strip())
                      return_data[key] = options
                  elif key == 'Bouwjaar':
                    if not 'construction_year' in return_data:
                      return_data['construction_year'] = value
                    else:
                      if not return_data['construction_year']:
                        return_data['construction_year'] = value
                  elif key == 'Kilometerstand':
                    if not 'mileage' in return_data:
                      return_data['mileage'] = value
                    else:
                      if not return_data['mileage']:
                        return_data['mileage'] = value
                  elif key == 'Uitvoering':
                    return_data['model_ex'] = value
                  elif key == 'Brandstof':
                    return_data['fuel'] = value
                  elif key == 'Transmissie':
                    return_data['transmission'] = value
                  elif key == 'Vermogen':
                    return_data['power'] = value
                  elif key == 'Topsnelheid':
                    return_data['speed'] = value
                  elif key == 'Prijs':
                    if not 'ad_price' in return_data:
                      return_data['ad_price'] = value
                    else:
                      if not return_data['ad_price']:
                        return_data['ad_price'] = value
                  else:
                    return_data[key] = value
              except:
                continue
      except:
        pass

    return return_data

  # get vehicle get_features_info
  def get_features_info(self, content):
    return_data = dict()
    if content:
      try:
        features_history_container = content.find(id="car-features-history")
        features_engine_container = content.find(id="car-features-engine")

        if features_history_container:
          features_table = features_history_container.find('div', class_="car-feature-table")
          if features_table:
            features = features_table.find_all('div', class_="row")
            for feature in features:
              key = feature.find('span', class_="key").text.strip()
              key = re.sub(r'\:', '', key).strip()
              value = feature.find('span', class_="value").text.strip()
              if key:
                if key == 'Eigenaar sinds':
                  return_data['owner_since'] = value
                if key == 'Datum registratie Nederland':
                  return_data['reg_date'] = value
                if key == 'Import auto':
                  return_data['imported'] = value
                if key == 'Nieuwprijs vanaf':
                  return_data['new_price'] = value
                else:
                  return_data[key] = value

        if features_engine_container:
          features_table = features_engine_container.find('div', class_="car-feature-table")
          if features_table:
            features = features_table.find_all('div', class_="row")
            for feature in features:
              key = feature.find('span', class_="key").text.strip()
              key = re.sub(r'\:', '', key).strip()
              value = feature.find('span', class_="value").text.strip()
              if key:
                if key == 'Koppel':
                  return_data['acceleration'] = value
                if key == 'CO2-uitstoot':
                  return_data['co2'] = value
                if key == 'Remmen voor':
                  return_data['break_front'] = value
                if key == 'Remmen achter':
                  return_data['break_back'] = value

      except:
        pass

    return return_data

  # get seller contact info (  )
  def get_contact_info(self, content):
    return_data = dict()

    if content:
      try:
        top_info = content.find('div', class_='top-info')
        if top_info:
          try:
            seller_name = top_info.find('h2', class_='name')
            if seller_name:
              return_data['seller_name'] = seller_name.text.strip()
          except:
            pass

          try:
            seller_url = top_info.find('a')
            if seller_url:
              return_data['seller_url'] = seller_url['href'].strip()
          except:
            pass

        seller_info = content.find('ul', class_='seller-info')
        if seller_info:
          try:
            vip_active_since = seller_info.find(id='vip-active-since')
            if vip_active_since:
              return_data['vip_active_since'] = re.sub(r'\s+', ' ', re.sub(r'½', '.5', vip_active_since.text.strip()) )
          except:
            pass

        vip_trust_indicate_group = content.find('div', class_='trust-indicator-group')
        if vip_trust_indicate_group:
          try:
            vip_trust_indicate_group_ul = vip_trust_indicate_group.find('ul')
            if vip_trust_indicate_group_ul:
              vip_trust_indicate_group_list = vip_trust_indicate_group_ul.find_all('li')
              groups = list()
              for item in vip_trust_indicate_group_list:
                groups.append(item.text.strip())
              return_data['trust_indicate_group'] = json.dumps(groups)
          except:
            pass
        
        vip_trust_indicate_ideal = content.find('div', class_='trust-indicator-ideal')
        if vip_trust_indicate_ideal:
          try:
            vip_trust_indicate_ideal_ul = vip_trust_indicate_ideal.find('ul')
            if vip_trust_indicate_ideal_ul:
              vip_trust_indicate_ideal_list = vip_trust_indicate_ideal_ul.find_all('li')
              ideals = list()
              for item in vip_trust_indicate_ideal_list:
                ideals.append(item.text.strip())
              return_data['vip_trust_indicate_ideal'] = json.dumps(ideals)
          except:
            pass
        
        try:
          vip_seller_location = content.find(id='vip-seller-location')
          if vip_seller_location:
            vip_seller_location_a = vip_seller_location.find('a')
            if vip_seller_location_a:
              return_data['location'] = vip_seller_location_a.text.strip()
              return_data['lat'] = vip_seller_location_a['lat'].strip()
              return_data['lng'] = vip_seller_location_a['long'].strip()
            else:
              return_data['location'] = vip_seller_location.text.strip()
        except:
          pass

        try:
          vip_seller_website = content.find(id='vip-seller-url')
          if vip_seller_website:
              vip_seller_url = vip_seller_website['data-url']
              if vip_seller_url:
                proxies = { 'http': self.get_random_proxy() }
                website_response = requests.get(vip_seller_url.strip(), proxies=proxies)
                if website_response:
                  return_data['seller_website'] = website_response.url
        except:
          pass

      except:
        pass

    return return_data
  
  # get all vehicle data
  def get_vehicle_data(self, vehicle_url):
    return_data = dict()
    return_data['ad_url'] = vehicle_url

    try:
      text = self.get_vehicle_page(vehicle_url)
      
      if text:

        ########################## convert string to DOM ########################
        soup = BeautifulSoup(text, 'lxml')
        
        # ########################## Get Main Container ########################
        main_container = soup.find('section', class_='l-main-left')
        aside_container = soup.find('aside', class_='l-side-right')
        
        ############### Get Main Vehicle Info #############
        if main_container:
          vehicle_text = main_container.find('section', class_='listing')
          
          if vehicle_text:
            l_top_content = vehicle_text.find('section', class_='l-top-content')
            l_bottom_content = vehicle_text.find('section', class_='l-body-content')
            
            # Get short link
            try:
              short_link = vehicle_text.find('div', class_='short-link')
              if short_link:
                link = short_link.find('input')['value'].strip()
                return_data['profile_link'] = link
            except:
              return_data['profile_link'] = vehicle_url

            if l_top_content:
              # get header container info ( title, view_count, favorited_count, displayed_since, price)
              header_info = self.get_header_info(l_top_content.find('section', class_='container-view-desktop'))
              return_data.update(header_info)

              # get gallery container info ( img, km_position, construction_year, consumption_KM/L, energy_label, guarantee )
              gallery_info = self.get_gallery_info(l_top_content.find('section', class_='gallery-container'))
              return_data.update(gallery_info)

            # get NAP status
            try:
              nap_container = re.search(r'NAP:', str(main_container))
              if nap_container:
                nap_text = str(main_container)[nap_container.span()[1] : nap_container.span()[1] + 300].strip()
                nap_text = nap_text.split('<')[0].strip()
                if nap_text:
                  return_data['NAP'] = nap_text
            except:
              pass

            if l_bottom_content:
              # get vehicle attributes info ()
              attr_info = self.get_attr_info(l_bottom_content.find(id="car-attributes"))
              return_data.update(attr_info)

              #get vehicle features info
              features_info = self.get_features_info(l_bottom_content.find(id="car-features"))
              return_data.update(features_info)

              # set plate_num and img save
              if 'Kenteken' in attr_info:
                return_data['plate_num'] = attr_info['Kenteken']

        ############### Get Seller Info #############
        if aside_container:
          contact_container = aside_container.find('section', class_='contact-info')
          vip_bidding_container = aside_container.find(id='vip-list-bids-block')

          if contact_container:
            # get seller contact info (  )
            contact_info = self.get_contact_info(contact_container.find(id='vip-seller'))
            return_data.update(contact_info)

          if vip_bidding_container:
            # get vip bid info 
            return_data['highest_bid'] = vip_bidding_container.text.strip()
        
        ############### Get Phone Number #############
        try:
          phone_num_pattern = re.search(r'initialPhoneNumber\s*\:?', text)

          phone_num_text = text[phone_num_pattern.span()[1] : phone_num_pattern.span()[1] + 20].split(',')[0]
          phone_num = re.search(r'\d+', re.sub(r'\'|\"|\+|\-|\_', '', phone_num_text))
          if phone_num:
            phone_num = phone_num.group().strip()
            return_data['cell'] = phone_num
        except:
          pass
        
        # get description data
        description_container = soup.find(id="vip-description")
        if description_container:
          try:
            # if mileage not exist
            if 'mileage' in return_data:
              if not return_data['mileage']:
                Tellerstand_text = re.search('Tellerstand\s*\:', str(description_container))
                if Tellerstand_text:
                  Tellerstand_text = str(description_container)[Tellerstand_text.span()[1] : Tellerstand_text.span()[1] + 30]
                  Tellerstand = re.search(r'\d+\.?\d+(km|Kilometer)', Tellerstand_text, re.I).group()
                  if Tellerstand:
                    return_data['mileage'] = Tellerstand

            # if phone num not exist
            mobile_num = ''
            if 'cell' in return_data:
              mobile_num = return_data['cell']
            else:
              mobile_num = ''
            if not mobile_num:
              mobile_num_text = re.search(r'(\d+\-?\d{8})|(\d+\-?\d{4})', str(description_container)).group()
              if mobile_num_text:
                return_data['cell'] = mobile_num_text
          except :
            pass

        # remove img url if plate_num not exist
        # if 'plate_num' in return_data:
        #   if return_data['plate_num'] == '':
        #     if 'imgs' in return_data:
        #       del return_data['imgs']

        # add date
        now = datetime.now()
        return_data['dtime'] = now.strftime("%d-%m-%Y %H:%M")

        return_data['Ad_category'] = "Auto's"
        
        return return_data
      else:
        return return_data

    except Exception as err:
      print('Error In Vehicle Data : ', err)
      return return_data
      
  def main(self):
    collection_links = self.db['links']
    collection_sold_cars = self.db['solds']
    collection_detail = self.db['details']

    for item in collection_links.find():
      self.url_list.append(item)
    print('URL Count : ', len(self.url_list))
    
    try:
      if len(self.url_list) > 0:
        for index,vehicle_url in enumerate(self.url_list):
          try:
            vehicle_data = self.get_vehicle_data(vehicle_url['link'])
            print('Crawled', str(index + 1), 'vehicles.')
            
            # exist vehicle url
            detail_query = {'ad_url':vehicle_url['link']}
            if 'ad_title' in vehicle_data:
              if collection_detail.count_documents(detail_query) > 0:
                if 'sold_status' in collection_detail.find_one(detail_query):
                  collection_detail.update_one(detail_query, { "$unset" : { 'sold_status' : ''}})
                if 'imgs' in vehicle_data:
                    del vehicle_data['imgs']
                collection_detail.update_one(detail_query, { "$set": vehicle_data })
              else:
                # img save
                try:
                  if 'Kenteken' in vehicle_data:
                    if 'imgs' in vehicle_data:
                      tmp_list = list()
                      for img in vehicle_data['imgs']:
                        extention = img.split('.')[-1]
                        img_name = str(uuid.uuid1())
                        urllib.request.urlretrieve("https:" + img, base_dir + "/car_imgs/" + img_name + "." + extention)
                        tmp_list.append(img_name + "." + extention)
                      if tmp_list:
                        vehicle_data['local_img_name'] = tmp_list
                        
                  if 'imgs' in vehicle_data:
                    del vehicle_data['imgs']
                except:
                  pass
                
                collection_detail.insert_one(vehicle_data)

            # not exist vehicle url (not found page)
            else:
              # for detail collection
              if collection_detail.count_documents(detail_query) > 0:
                collection_detail.update_one(detail_query, { "$set": { "sold_status": "SOLD" } })

              # for links collection
              link_query = {'link':vehicle_url['link']}
              if collection_links.count_documents(link_query) > 0:
                collection_links.delete_one(link_query)
                if collection_sold_cars.count_documents(link_query) == 0:
                  collection_sold_cars.insert_one({
                    'link' : vehicle_url['link'],
                    'dtime' : vehicle_data['dtime'],
                  })
          
          except :
            continue
      else:
        print('Not Found URL List. Please Check You Have URL List.')
    except Exception as err:
      print('Error in Main Function', err)
      
if __name__ == '__main__':
  crawlsystem = Crawlsystem()
  crawlsystem.main()