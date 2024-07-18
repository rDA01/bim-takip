from decimal import Decimal
from data.repositories.productRepository import ProductRepository
from data.entities.product import Product

import requests
from bs4 import BeautifulSoup
import re
import time
from service.telegramService import TelegramService

class ProductService:
    def __init__(self, repository: ProductRepository, telegram_service: TelegramService):
        self.repository = repository
        self.telegram_service = telegram_service
        self.base_url = "https://www.bim.com.tr/"
    async def updateProduct(self):
        
        links = self.repository.get_all_product_links()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'}
        for link in links:
            time.sleep(1)
            response = requests.get(self.base_url+ link,headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                try: 
                    price_cover = soup.find('div', class_='buttonArea col-12 col-lg-7 order-lg-1 order-2 aktuelFiyat')
                    price_details = price_cover.find('a',class_="gButton triangle")
                    price_div = price_details.find('div',class_="text quantify")
                except:
                    print(str(link))
                    print("couldnt find price")
                    pass
                
                if price_div:
                
                    price_text = price_div.text.strip()
                    price_text = price_text.replace('.', '').replace(',', '.')  # Replace comma with dot
                    price_numeric = float(''.join(filter(lambda x: x.isdigit() or x == '.', price_text)))
                    price_numeric = Decimal(price_numeric)
                    product = self.repository.get_product_by_link(link)
                    
                    
                    if product:
                        if product.price != price_numeric:
                            print("existing price: ", product.price, '\n', "new price: ", price_numeric)
                            
                            old_price = Decimal(product.price)
                            
                            price_numeric = Decimal(price_numeric)
                             
                            
                            product.price = Decimal(price_numeric)
                            self.repository.update_product(product)
                            isInstallment = Decimal(price_numeric) <= Decimal(old_price) * Decimal(0.92) 
                            if(isInstallment):
                                print("installment catched, product link: ", product.link)
                                installment_rate = ((old_price - Decimal(price_numeric)) / old_price) * 100
                                old_price = "{:.2f}".format(old_price) 
                                price_numeric = "{:.2f}".format(price_numeric)
                                installment_rate = "{:.1f}".format(installment_rate)
                                message = f"{str(self.base_url)+str(link)} linkli, {product.title} başlıklı ürünün fiyatında indirim oldu. Önceki fiyat: {old_price}, Yeni fiyat: {price_numeric}. İndirim oranı: %{installment_rate}"

                                await self.telegram_service.send_message(message)
                                   
                                
                        else:
                            print("Product price is remaining the same")
                    else:
                        print("Product not found in the database:", link)
                else:
                    print("No price span found.")
            else:
                print("Price box not found on the page:", link)
        else:
            print("Failed to retrieve page")
              

