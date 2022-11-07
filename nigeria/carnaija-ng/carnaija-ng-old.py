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
    start_urls = ["https://www.carnaija.com/buy-cars?page=23"]

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

        title = tree.xpath(
            '//div[@class="ad-title"]/h2/text()'
        ).extract_first()  # include "make","model"
        # "self.double_word_cars" -> Vehicle name containing all two words of this website
        judge_make = [
            i for i in self.double_word_cars if i in title
        ]  # Determine whether the vehicle name is two words
        if judge_make:  # If two words,Get "make" directly from the list
            output["make"] = judge_make[0]
            output["model"] = title.replace(output["make"], "", 1).strip()
        else:  # If one words,Get "make" directly from the title
            output["make"] = re.findall("ad-(.*?)-", response.url, re.S)[0].capitalize()
            output["model"] = title.replace(output["make"], "", 1).strip()

        form_data = tree.xpath("//div[@class='vehicle-properties']/div")  # data form
        for i in form_data:
            key = i.xpath("./div/span[1]/@title").extract_first()
            value = i.xpath("./div/span[2]/@title").extract_first()
            if "N/A" in value:
                continue
            if "Year" in str(key):
                output["year"] = int(value)
            elif "Gearbox" in str(key):  # transmission
                output["transmission"] = value
            elif "Engine" in str(key):
                output["engine_displacement_value"] = value.split(" ")[0]
                output["engine_displacement_units"] = value.split(" ")[1]
            elif "Fuel" in str(key):
                output["fuel"] = value
            elif "Mileage" in str(key):
                output["odometer_value"] = int(value.split(" ")[0].replace(",", ""))
                output["odometer_unit"] = value.split(" ")[1]

        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "CarnaijaCOM"
        output["scraped_listing_id"] = response.url.split("-")[-1]
        output["vehicle_url"] = response.url
        output["city"] = tree.xpath(
            "//div[@class='ad-title']/a/span/text()"
        ).extract_first()
        output["country"] = "Nigeria"
        price = tree.xpath(
            "//div[@class='md-hidden col-lg-4 col-xl-3']//span[@class='price-wrap ']/span/text()"
        ).extract_first()
        if price:  # maybe null
            output["price_retail"] = float(price.replace(",", ""))
            output["price_wholesale"] = float(price.replace(",", ""))
            output["currency"] = (
                tree.xpath(
                    "//div[@class='md-hidden col-lg-4 col-xl-3']//span[@class='price-wrap ']/text()"
                )
                .extract_first()
                .strip()
            )

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
        # yield output
