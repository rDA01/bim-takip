import asyncio
import logging
import requests
from bs4 import BeautifulSoup
import threading

from data.entities.product import Product
from data.repositories.productRepository import ProductRepository
from service.productService import ProductService
from service.telegramService import TelegramService

import time
import random

class LoggingConfigurator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        handler = logging.FileHandler('application.log')
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

class GatherPagesItems(LoggingConfigurator):
    def __init__(self, product_repo,url):
        self.base_url=url
        self.page_count=0
        self.item_count=0
        self.product_repo = product_repo

    async def gather_page_number(self, base_url):
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'}
        response = requests.get(base_url,headers=headers)

        if response.status_code == 200:
            try:

                
                soup = BeautifulSoup(response.content, 'html.parser')
                content = soup.find('div',class_="container content white no-pb")
                row = content.find('div',class_="row")
                divs = list()
                newdivs = row.find_all('div', class_='product col-xl-3 col-lg-3 col-md-4 col-sm-6 col-12')
                for div in newdivs:
                    divs.append(div)
                
                for i in range(23):
                    newdivs = row.find_all('div', class_='product col-xl-3 col-lg-3 col-md-4 col-sm-6 col-12 LoadGroup'+str(i))
                    for div in newdivs:
                
                        divs.append(div)

                

                for div in divs:
                   
                    h2 = div.find('h2',class_='title')
            
                    details = div.find('div',class_="col-6 col-sm-12 col-lg-12 imageArea")
                    link = details.find('a')
                    prc_span = div.find('div',class_="text quantify").get_text()
                    

                    if h2 and link and prc_span:
                        title = h2.get_text()                
                        href = link['href']
                        if("telefon" in title.lower()):
                                 
                            item =  self.product_repo.get_product_by_link(href)
                            
                            price_text = prc_span
                            price_text = price_text.replace('.', '').replace(',', '.')  # Replace comma with dot
                            price = float(''.join(filter(lambda x: x.isdigit() or x == '.', price_text)))                        
                        
                            if item is False:
                                product = Product(id=None,title=title, link=href, price=price)
                                self.product_repo.add_product(product)
                                print("Added: ", title)
                        else:                           
                            print("Item Skipped")
            except Exception as err:
                print("Error occurred:", err)
                return False
        else:
            print("Couldnt Retrive Page")
            return False
            


               
     
        return True

    async def gather_page_numbers(self):
        base_url = self.base_url
        
        await self.gather_page_number(base_url)
    

async def Main():
    product_repo = ProductRepository()

    smartphones = GatherPagesItems(product_repo,"https://www.bim.com.tr/Categories/100/aktuel-urunler.aspx?top=1&Bim_AktuelTarihKey=100")
    
    await smartphones.gather_page_numbers()

    
    telegram_service = TelegramService(bot_token='7393980187:AAGJHwoW6DY98jZOvTzdq0o7Ojt8X1VO28Q', chat_id='-1002203530212')
    
    productService = ProductService(product_repo, telegram_service)
    
    while True:
        await productService.updateProduct()
    

asyncio.run(Main())