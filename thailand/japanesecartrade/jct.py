import datetime
import json
import re
import scrapy
from scrapy.selector import Selector

# import apify


class BeforwardSpider(scrapy.Spider):
    name = "beforward"
    download_timeout = 120
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"

    def start_requests(self):
        urls = [
            "https://www.japanesecartrade.com/stock_list.php?make_id=&maker_id=&mfg_from=&month_from=&mfg_to=&month_to=&fuel_id=&seat_capacity=&transmission_id=&type_id=&subtype_id=&drive=&mileage_from=&mileage_to=&price_from=&price_to=&cc_from=&cc_to=&wheel_drive=&color_id=&stock_country=thailand&search_keyword=&SA=make&isSearched=1&sort=&desksearch=desksearch&seq=&page=0"
        ]

        for url in urls:
            country = ""
            country_name = url.split("stock_country=")[1]
            if "uae" in country_name:
                country = "AE"
            elif "uk" in country_name:
                country = "GB"
            elif "korea" in country_name:
                country = "KR"
            elif "japan" in country_name:
                country = "JP"
            elif "thailand" in country_name:
                country = "TH"
            elif "singapore" in country_name:
                country = "SG"
            elif "kenya" in country_name:
                country = "KE"

            yield scrapy.Request(
                url=url,
                meta={"country": country},
                callback=self.parse,
            )

    def parse(self, response):
        # Traverse product links
        product_links = response.xpath('//h2[@class="list_head"]/a/@href').getall()
        yield from response.follow_all(
            product_links,
            meta={"country": response.meta["country"]},
            callback=self.detail,
        )

        # pagination
        page_link = response.xpath('//ul[@class="pagination"]/li[11]/a/@href').get()
        print(page_link)
        if page_link is not None:
            yield response.follow(
                page_link,
                meta={"country": response.meta["country"]},
                callback=self.parse,
            )

    def detail(self, response):
        output = {}
