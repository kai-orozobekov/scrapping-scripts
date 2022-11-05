import scrapy
import json
import datetime
import re
import requests
from scrapy import Selector, Request

import apify


class AutotraderSpider(scrapy.Spider):
    name = "autotrader"
    download_timeout = 120
    start_urls = [
        "https://www.autotrader.ca/cars/?rcp=15&rcs=0&srt=35&prx=-1&hprc=True&wcp=True&iosp=True&sts=Used&inMarket=advancedSearch",
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, cb_kwargs={"page": 1})

    def parse(self, response, page):
        product_links = response.xpath(
            '//div[@id="SearchListings"]/div/div[2]/div[2]/div/div/h2/a/@href'
        ).getall()
        yield from response.follow_all(product_links, self.product_detail)

        if product_links:
            page += 1
            rcp = (page - 1) * 15
            page_link = f"https://www.autotrader.ca/cars/?rcp=15&rcs={rcp}&srt=35&prx=-1&hprc=True&wcp=True&iosp=True&sts=Used&inMarket=advancedSearch"
            yield response.follow(
                url=page_link, callback=self.parse, cb_kwargs={"page": page}
            )

    def product_detail(self, response):
        ex = "window\['ngVdpModel']\ = (.*?)window\['ngVdpGtm'\]"
        jsn = re.findall(ex, response.text, re.S)[0]
        # Re parsing JSON of product details
        jsn = jsn[::-1].replace(";", "", 1)[::-1].strip()
        jsn = json.loads(jsn)

        transmission = None
        engine = None
        fuel = None
        specs = jsn["specifications"].get("specs")
        for data in specs:  # Cycle the specs list to get the required field data
            if data["key"] == "Transmission":
                transmission = data["value"]
            if data["key"] == "Engine":
                engine = data["value"]
            if data["key"] == "Fuel Type":
                fuel = data["value"]

        mileage = jsn["hero"].get("mileage")  # Vehicle mileage，Need to make judgment
        odometer_value = None
        odometer_unit = None
        if "km" in str(mileage):  # Judge mileage
            odometer_value = mileage.split(" ")[0]
            odometer_unit = mileage.split(" ")[1]
        elif "N/A" in str(mileage):
            odometer_value = mileage

        picture_list_items = jsn["gallery"].get("items")  # picture list
        picture_list = [
            picture.get("photoViewerUrl")
            for picture in picture_list_items
            if picture.get("type") == "Photo"
        ]

        city = jsn["deepLinkSavedSearch"]["savedSearchCriteria"].get("city")  # city
        countryName = "Canada"

        price_mark = jsn["adBasicInfo"].get(
            "price"
        )  # Currency symbols to judge currency abbreviations
        currency = None
        if "$" in price_mark:
            currency = "USD"

        output = {
            "vin": jsn["hero"].get("vin"),
            "make": jsn["hero"].get("make"),
            "model": jsn["hero"].get("model"),
            "year": int(jsn["hero"].get("year")),
            "trim": jsn["hero"].get("trim"),
            "transmission": transmission,
            "engine_displacement_value": engine,
            "fuel": fuel,
            "ac_installed": 0,
            "tpms_installed": 0,
            "scraped_date": datetime.datetime.isoformat(datetime.datetime.today()),
            "scraped_from": "AutoTrader",
            "scraped_listing_id": str(jsn["adBasicInfo"].get("adId")),
            "odometer_value": int(odometer_value.replace(",", "")),
            "odometer_unit": odometer_unit,
            "vehicle_url": response.url,
            "picture_list": json.dumps(picture_list),
            "city": city,
            "country": countryName,
            "price_retail": float(jsn["hero"].get("price").replace(",", "")),
            "price_wholesale": float(jsn["hero"].get("price").replace(",", "")),
            "currency": currency,
        }
        list1 = []
        list2 = []
        for k, v in output.items():
            if v is not None:
                list1.append(k)
                list2.append(v)
        output = dict(zip(list1, list2))

        # yield output
        apify.pushData(output)
