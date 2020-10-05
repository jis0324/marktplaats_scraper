# from selenium import webdriver
import time
import random
import os
from bs4 import BeautifulSoup
import csv
import requests
import re
import pymongo
from datetime import datetime
import threading
# mongoclient = pymongo.MongoClient("mongodb+srv://***")
mongoclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongoclient["mp_ads_scraper"]

base_dir = os.path.dirname(os.path.abspath(__file__))

class Crawlsystem(object):
  def __init__(self):
    global base_dir, db
    self.proxy_list = list()
    self.page_source = ''
    self.url_list = list()
    self.db = db
    self.collection_detail_links = self.db['detail_links']
    self.collection_details = self.db['details']
    self.get_proxy_list()
    self.detail_links_list = list()

  def get_proxy_list(self):
    collection = self.db['proxies']
    proxy_list = collection.find()
    for proxy in proxy_list:
      self.proxy_list.append(proxy['proxy'])

  def get_random_proxy(self):
    random_idx = random.randint(0, len(self.proxy_list)-1)
    proxy_ip = self.proxy_list[random_idx]
    return proxy_ip

  # def get_detail_data(self, detail_url, detail_category):
  def get_detail_data(self):
    while True:
      if len(self.detail_links_list) == 0:
        return

      detail_link = self.detail_links_list[0]
      del self.detail_links_list[0]

      detail_url = detail_link['link']
      detail_category = detail_link['ad_category']
      
      return_data = {
        'profile_link' : '',
        'name' : '',
        'cell' : '',
        'location' : '',
        'lat' : '',
        'lng' : '',
        'seller_website' : '',
        'title' : '',
        'category' : '',
        'views' : '',
        'likes' : '',
        'posted_date' : '',
        'price' : '',
        'highest_bid' : '',
        'ad_url' : detail_url,
        'dtime' : '',
        'status_code': '',
      }

      try:
        proxies = { 'http': self.get_random_proxy() } 
        # print('Selected Proxies : ', proxies)

        r = requests.get(detail_url, proxies=proxies)
        text = r.text
        return_data['status_code'] = r.status_code
        
        if text:
          ########################## convert string to DOM ########################
          soup = BeautifulSoup(text, 'lxml')
          
          try:
            return_data['profile_link'] = soup.find(id="vip-seller").find('div', class_="top-info").find('a')['href'].strip()
          except:
            pass
          
          try:
            return_data['name'] = soup.find(id="vip-seller").find('div', class_="top-info").find('h2', class_='name').text.strip()
          except:
            pass
          
          try:
            phone_num_pattern = re.search(r'initialPhoneNumber\s*\:?', text)

            phone_num_text = text[phone_num_pattern.span()[1] : phone_num_pattern.span()[1] + 20].split(',')[0]
            phone_num = re.search(r'\d+', re.sub(r'\'|\"|\+|\-|\_', '', phone_num_text))
            if phone_num:
              phone_num = phone_num.group().strip()
              return_data['cell'] = phone_num
          except:
            pass

          try:
            vip_seller_location = soup.find(id='vip-seller-location')
            if vip_seller_location:
              vip_seller_location_a = vip_seller_location.find('a')
              if vip_seller_location_a:
                try:
                  return_data['location'] = vip_seller_location_a.text.strip()
                except:
                  pass
                try:
                  return_data['lat'] = vip_seller_location_a['lat'].strip()
                except:
                  pass
                try:
                  return_data['lng'] = vip_seller_location_a['long'].strip()
                except:
                  pass
              else:
                return_data['location'] = vip_seller_location.text.strip()
          except:
            pass

          try:
            vip_seller_website = soup.find(id='vip-seller-url')
            if vip_seller_website:
                vip_seller_url = vip_seller_website['data-url']
                if vip_seller_url:
                  proxies = { 'http': self.get_random_proxy() }
                  website_response = requests.get(vip_seller_url.strip(), proxies=proxies)
                  if website_response:
                    return_data['seller_website'] = website_response.url
          except:
            pass
          
          try:
            ############## Get Title ###############
            title = soup.find(id="title")
            if title:
              return_data['title'] = title.text.strip()
          except:
            pass
            
          # try:
          #   short_link = soup.find('div', class_='short-link')
          #   if short_link:
          #     ad_url = short_link.find('input')['value'].strip()
          #     return_data['ad_url'] = ad_url
          #   else:
          #     return_data['ad_url'] = detail_url
          # except :
          #   pass

          try:
            return_data['category'] = detail_category
          except:
            pass
          
          try:
            view_count = soup.find(id="view-count")
            if view_count:
              return_data['views'] = view_count.text.strip()
          except:
            pass

          try:
            favorited_count = soup.find(id="favorited-count")
            if favorited_count:
              return_data['likes'] = favorited_count.text.strip()
          except:
            pass
          
          try:
            displayed_since = soup.find(id="displayed-since")
            if displayed_since:
              return_data['posted_date'] = re.sub(r'\s+', ' ', displayed_since.text.strip())
          except:
            pass
          
          try:
            price = soup.find(id="vip-ad-price-container")
            if price:
              return_data['price'] = price.text.strip()
          except:
            pass
          
          try:
            vip_bidding_container = soup.find(id='bids-overview')
            if vip_bidding_container:
              bid_ul = vip_bidding_container.find_all('li', class_='bid')
              if bid_ul:
                temp_list = list()
                for li in bid_ul:
                  temp_list.append(li.text.strip())
                return_data['highest_bid'] = temp_list
              else:
                return_data['highest_bid'] = vip_bidding_container.text.strip()
          except:
            pass
          
          now = datetime.now()
          return_data['dtime'] = now.strftime("%d-%m-%Y %H:%M")

      except Exception as err:
        print('Error In detail Data : ', err)
        return_data['status_code'] = 404

      try:
        if return_data['status_code'] == 200:
          del return_data['status_code']

          if return_data['title']:
            if self.collection_details.count_documents({'ad_url' : detail_url}) == 0:
              self.collection_details.insert_one(return_data)
            else:
              if 'sold_status' in self.collection_details.find_one({'ad_url' : detail_url}):
                self.collection_details.update_one({'ad_url' : detail_url}, { "$unset" : { "sold_status": "" }})
              self.collection_details.update_one({'ad_url' : detail_url}, { "$set" : return_data})
          else:
            if self.collection_details.count_documents({'ad_url' : detail_url}) > 0:
              self.collection_details.update_one({'ad_url' : detail_url}, { "$set" : { "sold_status": "SOLD" }})
              if self.collection_detail_links.count_documents({'link':detail_url}) > 0:
                self.collection_detail_links.delete_one({'link':detail_url})
        else:
          # print('*****', return_data, '*****')
          pass

        print('Total URLs : ', self.total_url_list_len, ' / Remain URLs : ', len(self.detail_links_list))      
      except Exception as err:
        print('Error in Main Function :', err)
        continue
      

  def main(self):
    for detail_link in self.collection_detail_links.find():
      temp_dict = {
        'link' : detail_link['link'],
        'ad_category' : detail_link['ad_category']
      }
      self.detail_links_list.append(temp_dict)
    
    self.total_url_list_len = len(self.detail_links_list)

    for x in range(10):
      thread = threading.Thread(target=self.get_detail_data)
      thread.start()
      time.sleep(2)

    # detail_links_list = self.collection_detail_links.find()
    # total_url_list_len = self.collection_detail_links.count_documents({})
    # print('Total Url List : ', total_url_list_len)

    # for index,detail in enumerate(detail_links_list):
    #   try:
    #     detail_data = self.get_detail_data(detail['link'], detail['ad_category'])
        
    #     if detail_data['status_code'] == 200:
    #       del detail_data['status_code']

    #       if detail_data['title']:
    #         if self.collection_details.count_documents({'ad_url' : detail['link']}) == 0:
    #           self.collection_details.insert_one(detail_data)
    #         else:
    #           if 'sold_status' in self.collection_details.find_one({'ad_url' : detail['link']}):
    #             self.collection_details.update_one({'ad_url' : detail['link']}, { "$unset" : { "sold_status": "" }})
    #           self.collection_details.update_one({'ad_url' : detail['link']}, { "$set" : detail_data})
    #       else:
    #         if self.collection_details.count_documents({'ad_url' : detail['link']}) > 0:
    #           self.collection_details.update_one({'ad_url' : detail['link']}, { "$set" : { "sold_status": "SOLD" }})
    #           if self.collection_detail_links.count_documents({'link':detail['link']}) > 0:
    #             self.collection_detail_links.delete_one({'link':detail['link']})
    #     else:
    #       print('*****', detail_data, '*****')

    #     print('Crawled : ', total_url_list_len, '/', index+1)      
    #   except Exception as err:
    #     print('Error in Main Function :', err)
    #     continue
      
if __name__ == '__main__':
  crawlsystem = Crawlsystem()
  crawlsystem.main()
