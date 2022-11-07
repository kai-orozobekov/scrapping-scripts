import re
import math
import json
import scrapy
import datetime
import requests
from scrapy import Selector

# import apify


class CarnaijaSpider(scrapy.Spider):
    name = "carnaija"
    download_timeout = 120
    # remove on Apify
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
    start_urls = ["https://www.carnaija.com/buy-cars?page=1"]

    def __init__(self):
        # Two word car model for example   'Alfa Romeo'  'Land Rover' 'De Tomaso' ....
        # Used to judge vehicle type,,Namely "make" field
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
        }
        double_word_cars = requests.get(
            url="https://www.carnaija.com/api/v1/listing/available-search-data/car-type-brands/car?_=1659669849577",
            headers=headers,
        ).json()
        self.double_word_cars = [
            i["name"] for i in double_word_cars if " " in i["name"]
        ]
        self.double_word_cars.append("Mercedes-Benz")

    def parse(self, response):
        tree = Selector(response)  # create Selector

        # etermine whether it is the last page
        last_page = tree.xpath("//h1[@class='count-cars']/text()").extract_first()
        last_page = math.ceil(
            int("".join([i for i in list(last_page) if i.isdigit()])) / 20
        )

        current_page = str(response.url).split("page=")[1]

        # detail url list
        link_list = tree.xpath('//div[@class="ads-lists"]/a/@href').extract()
        link_list = ["https://www.carnaija.com" + i for i in link_list]

        yield from response.follow_all(link_list, self.product_detail)

        # Determine whether the next page exists
        if int(current_page) + 1 < int(last_page) + 1:
            new_list_link = (
                response.url.split("page=")[0] + "page=" + str(int(current_page) + 1)
            )
            yield response.follow(new_list_link, self.parse)

    def product_detail(self, response):
        output = {}
        tree = Selector(response)  # create Selector

        # include "make","model"
        title = tree.xpath('//div[@class="ad-title"]/h2/text()').extract_first()

        # "self.double_word_cars" -> Vehicle name containing all two words of this website
        judge_make = [i for i in self.double_word_cars if i in title]

        # Determine whether the vehicle name is two words
        if judge_make:
            # If two words,Get "make" directly from the list
            output["make"] = judge_make[0]
            output["model"] = title.replace(output["make"], "", 1).strip()
        else:
            # If one words, Get "make" directly from the title
            output["make"] = re.findall("ad-(.*?)-", response.url, re.S)[0].capitalize()
            output["model"] = title.replace(output["make"], "", 1).strip()

        output["ac_installed"] = 0
        output["tpms_installed"] = 0

        form_data = tree.xpath("//div[@class='vehicle-properties']/div")
        for i in form_data:
            key = str(i.xpath("./div/span[1]/@title").extract_first()).lower()
            value = i.xpath("./div/span[2]/@title").extract_first()

            if "N/A" in value:
                continue
            if "year" == key:
                output["year"] = int(value)

            elif "gearbox" == key:
                output["transmission"] = value

            elif "engine" in key:
                output["engine_displacement_value"] = value.split(" ")[0]
                output["engine_displacement_units"] = value.split(" ")[1]

            elif "fuel type" == key:
                output["fuel"] = value

            elif "body type" == key:
                output["body_type"] = value

            elif "drive type" == key:
                output["steering_position"] = value

            elif "color" == key:
                if value.lower() != "other":
                    output["exterior_color"] = value

            elif "condition" == key:
                if value.lower() == "used":
                    output["is_used"] = 1
                elif value.lower() == "new":
                    output["is_used"] = 0

            elif "air con" == key:
                if value.lower() == "yes":
                    output["ac_installed"] = 1

            elif "mileage" == key:
                output["odometer_value"] = int(value.split(" ")[0].replace(",", ""))
                output["odometer_unit"] = value.split(" ")[1]

        # scraping info
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "CarnaijaCOM"
        output["scraped_listing_id"] = response.url.split("-")[-1]
        output["vehicle_url"] = response.url

        # location details
        output["city"] = tree.xpath(
            "//div[@class='ad-title']/a/span/text()"
        ).extract_first()
        output["country"] = "Nigeria"

        # price details
        price_field = tree.xpath(
            "//div[@class='md-hidden col-lg-4 col-xl-3']//span[@class='price-wrap ']"
        )
        price = price_field.xpath("./span/text()").extract_first()
        currency = price_field.xpath("./text()").extract_first().strip()
        if price:
            output["price_retail"] = float(price.replace(",", ""))
            output["currency"] = currency

        pic = tree.xpath("//div[@class='carousel-wrapper']//img/@data-src").extract()
        # A blank photo URL
        blank_pic = "https://carnaija.com/assets/fallback/vehicle-listing-c86a209c3f7abd2f4c942821bb03979da9517370dd7124d54945d68e339bb0ad.png"
        if blank_pic in pic:
            pic = pic.remove(blank_pic)

        if pic:
            output["picture_list"] = json.dumps(list(set(pic)))

        # process empty fields
        list1 = []
        list2 = []
        for k, v in output.items():
            if v or v == 0:
                list1.append(k)
                list2.append(v)
        output = dict(zip(list1, list2))

        # apify.pushData(output)
