import scrapy
import datetime
import json
import requests

# import apify


def generate_record(city_obj: dict, record_obj: dict):
    url = f"https://www.cars24.com/buy-used-{record_obj['make']}-{record_obj['model'].replace(' ', '-')}-{record_obj['year']}-cars-{city_obj['cityName']}-{record_obj['carId']}/"
    meta = {}
    meta["city"] = city_obj["cityName"]
    if "bodyType" in record_obj:
        meta["bodyType"] = record_obj["bodyType"]
    if "fuelType" in record_obj:
        meta["fuel"] = record_obj["fuelType"]
    if "kilometerDriven" in record_obj:
        meta["kilometerDriven"] = record_obj["kilometerDriven"]
    if "originalPrice" in record_obj:
        meta["retailPrice"] = record_obj["originalPrice"]
    if "onRoadPrice" in record_obj:
        meta["promotionalPrice"] = record_obj["onRoadPrice"]
    if "make" in record_obj:
        meta["make"] = record_obj["make"]
    if "model" in record_obj:
        meta["model"] = record_obj["model"]
    if "transmission" in record_obj:
        meta["transmission"] = record_obj["transmission"]
    if "variant" in record_obj:
        meta["trim"] = record_obj["variant"]
    if "year" in record_obj:
        meta["year"] = record_obj["year"]
    return {
        "link": url,
        "meta": meta,
    }


class Car24(scrapy.Spider):
    name = "cars24"
    download_timeout = 120
    start_urls = ["https://oms-aggregator-service.c24.tech/api/v1/cities"]
    individual_links = []

    def parse(self, response):
        cities = response.json()
        for city in cities:
            first_page_data = requests.get(
                f"https://api-sell24.cars24.team/buy-used-car?sort=P&serveWarrantyCount=false&gaId=136166958.1674796566&page=1&storeCityId={city['cityId']}"
            ).json()
            total_pages = int(first_page_data["data"]["totalPages"])
            for record in first_page_data["data"]["content"]:
                generated_record = generate_record(city, record)
                self.individual_links.append(generated_record)
            for i in range(2, total_pages + 1):
                page_data = requests.get(
                    f"https://api-sell24.cars24.team/buy-used-car?sort=P&serveWarrantyCount=false&gaId=136166958.1674796566&page={i}&storeCityId={city['cityId']}"
                ).json()
                for record in page_data["data"]["content"]:
                    generated_record = generate_record(city, record)
                    self.individual_links.append(generated_record)

        for record in self.individual_links:
            yield response.follow(
                record["link"],
                meta=record["meta"],
                callback=self.product_detail,
            )

    def product_detail(self, response):
        output = {}
        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        meta = response.meta
        # scraping info
        output["vehicle_url"] = response.url
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "Cars24"
        output["scraped_listing_id"] = response.url.split("-")[-1].replace("/", "")

        # location info
        output["city"] = meta["city"]
        output["country"] = "IN"

        # basic info
        if "make" in meta:
            output["make"] = meta["make"]
        if "model" in meta:
            output["model"] = meta["model"]
        if "trim" in meta:
            output["trim"] = meta["trim"]
        if "year" in meta:
            output["year"] = int(meta["year"])

        # odometet info
        if "kilometerDriven" in meta:
            output["odometer_value"] = int(meta["kilometerDriven"])
            output["odometer_unit"] = "km"
        
        # other data
        if "transmission" in meta:
            output["transmission"] = meta["transmission"]
        if "fuel" in meta:
            output["fuel"] = meta["fuel"]
        if "bodyType" in meta:
            output["body_type"] = meta["bodyType"]

        # pricing details
        if "retailPrice" in meta:
            output["price_retail"] = float(meta["retailPrice"])
            output["currency"] = "INR"
        if "promotionalPrice" in meta:
            if meta["promotionalPrice"] != meta["retailPrice"]:
                output["promotional_price"] = float(meta["promotionalPrice"])

        # pictures
        picture_list = response.xpath("//div[@class='_2H6d9']//img/@src").getall()
        if picture_list:
            output["picture_list"] = json.dumps(picture_list)

        # apify.pushData(output)
