import scrapy
import json
import datetime
import datetime

# import apify


class TuMakina(scrapy.Spider):
    name = 'tumakina'
    download_timeout = 120
    id = 0
    type_list = ['1', '2', '3', '4', '5', '8']
    start_urls = ["https://tumakina.com/ajax-more.php"]
    headers = {"Host": "tumakina.com",
               "Content-Length": '347',
               }
    body = {"term": "",
            "type": "",
            "brand": "",
            "model": "",
            "year": "",
            "province": "",
            "sorting": "low",
            "engine": "",
            "gas": "",
            "traction": "",
            "mileage": "",
            "oferta": '0',
            "garantia": '0',
            "piel": '0',
            "asientos": '0',
            "llave": '0',
            "sunroof": '0',
            "camara": '0',
            "pantalla": '0',
            "applecar": '0',
            "asientosfilas": '0',
            "page": '0',
            "currentYear": datetime.datetime.now().strftime('%Y'),
            "price": "",
            "ordenar": "",
            "provincemobile": "",
            "pricemobile": "",
            "marcamoto": "",
            "modelomoto": "",
            "marcamontacargas": "",
            "modelomontacargas": "",
            "marcaplantas": "",
            "modeloplantas": ""
            }
    
    def start_requests(self):
        type = self.type_list[0]
        del self.type_list[0]
        self.body['type'] = type
        yield scrapy.FormRequest(url=self.start_urls[0],
                                 method='POST',
                                 headers=self.headers,
                                 formdata=self.body,
                                 callback=self.parse)
            
        
        
    def parse(self, response):
        # Traverse product links
        product_links = response.xpath("//div[@class='fila']/a/@href").getall()
        yield from response.follow_all(product_links, callback=self.detail)
        
        # pagination
        id = response.xpath("//span[@class='show_more']/@id").get()
        data_year = response.xpath("//span[@class='show_more']/@data-year").get()
        if id is not None:
            if id != self.id:
                self.id =id
                self.body['page'] = str(id)
                self.body['currentYear'] = str(data_year)
                yield scrapy.FormRequest(url="https://tumakina.com/ajax-more.php",
                                         method='POST',
                                         headers=self.headers,
                                         formdata=self.body,
                                         callback=self.parse)
        # Traverse the next type
        elif len(self.type_list) > 0:
            self.id =0
            self.body['page'] = '0'
            self.body['currentYear'] = datetime.datetime.now().strftime('%Y')
            type = self.type_list[0]
            del self.type_list[0]
            self.body['type'] = type
            yield scrapy.FormRequest(url="https://tumakina.com/ajax-more.php",
                                         method='POST',
                                         headers=self.headers,
                                         formdata=self.body,
                                         callback=self.parse)
            
        
    
    def detail(self, response):       
        output = {}
        
        if response.xpath("//span[@id='txtMarca']/text()").get() is not None:
            output['make'] = response.xpath("//span[@id='txtMarca']/text()").get()
            
        if response.xpath("//span[@id='txtModelo']/text()").get() is not None:
            output['model'] = response.xpath("//span[@id='txtModelo']/text()").get()
            
        if response.xpath("//span[@class='edicion']/text()").get() is not None:
            output['model'] = output['model'] + ' ' + response.xpath("//span[@class='edicion']/text()").get().strip()
            
        if response.xpath("//span[@id='txtAno']/text()").get() is not None:
            if response.xpath("//span[@id='txtAno']/text()").get().replace('\n', '') != '':
                output['year'] = int(response.xpath("//span[@id='txtAno']/text()").get().replace('\n', ''))
        
        
        for i in range(1, len(response.xpath("//table/tr").getall())+1):
            if response.xpath(f"//table/tr[{i}]/td[2]/text()").get() or response.xpath(f"//table/tr[{i}]/td[2]/span/text()").get():
                if response.xpath(f"//table/tr[{i}]/td[1]/text()").get() == 'Motor':
                    if response.xpath(f"//table/tr[{i}]/td[2]/text()").get().replace('\n', '').strip():
                        output['engine_displacement_value'] = response.xpath(f"//table/tr[{i}]/td[2]/text()").get().replace('\n', '').strip()
                        output['engne_displacement_units'] = output['engine_displacement_value'].split(' ')[-1]
                    
                elif response.xpath(f"//table/tr[{i}]/td[1]/text()").get() == 'Combustible':
                    output['fuel'] = response.xpath(f"//table/tr[{i}]/td[2]/span/text()").get().replace('\n', '').strip()
                    
                elif response.xpath(f"//table/tr[{i}]/td[1]/text()").get() == 'Transmisión':
                    output['transmission'] = response.xpath(f"//table/tr[{i}]/td[2]/text()").get().replace('\n', '').strip()
                    
                    
        output['ac_installed'] = 0
        output['tpms_installed'] = 0
        output['scraped_date'] = datetime.datetime.isoformat(datetime.datetime.today())
        output['scraped_from'] = 'tuMakina'
        output['scraped_listing_id'] = response.xpath("//div[@class='registro']/text()").get().replace('Reg. No.', '').strip()
        output['vehicle_url'] = response.url
        
        pictures = response.xpath("//div[@class='item']/a/@href").getall()
        if len(pictures) == 0:
            pictures.extend(response.xpath("//a[@class='mainphoto ']/@href").get())
        output['picture_list'] = json.dumps(["https://tumakina.com/"+url for url in pictures])
        
        output['city'] = response.xpath("//p[@class='ciudad']/text()").get()
        output['country'] = 'Dominican Republic'
        if response.xpath("//div[@class='precio']/text()").getall()[1].strip() != '':
            if "RD" in response.xpath("//div[@class='precio']/text()").getall()[1]:
                output['currency'] = 'RD'
            elif "US" in response.xpath("//div[@class='precio']/text()").getall()[1]:
                output['currency'] = 'USD'
            output['price_retail'] = float(response.xpath("//div[@class='precio']/text()").getall()[1].replace('US', '').replace('$', '').replace(',', '').replace('RD', '').strip())
            output['price_wholesale'] = output['price_retail']
        
        # process empty fields
        list1 = []
        list2 = []
        for k, v in output.items():
            if v is not None:
                list1.append(k)
                list2.append(v)
        output = dict(zip(list1, list2))
        
        # yield output
        # apify.pushData(output)
