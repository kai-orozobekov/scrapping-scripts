import datetime
import json
import re
import scrapy
from scrapy.selector import Selector

# import apify


class BeforwardSpider(scrapy.Spider):
    name = "beforward"
    download_timeout = 120

    def start_requests(self):
        urls = [
            "https://www.beforward.jp/stocklist/page=1/sortkey=a/stock_country=47",
        ]

        for url in urls:
            country = ""
            country_code = int(url.split("stock_country=")[1])
            if country_code == 44:
                country = "AE"
            elif country_code == 35:
                country = "SG"
            elif country_code == 41:
                country = "TH"
            elif country_code == 45:
                country = "GB"
            elif country_code == 28:
                country = "KR"
            elif country_code == 47:
                country = "JP"

            yield scrapy.Request(
                url=url,
                meta={"country": country},
                callback=self.parse,
            )

    def parse(self, response):
        # Traverse product links
        product_links = response.xpath('//p[@class="make-model"]/a/@href').getall()
        yield from response.follow_all(
            product_links,
            meta={"country": response.meta["country"]},
            callback=self.detail,
        )

        # pagination
        page_link = response.xpath('//a[@class="pagination-next"]/@href').get()
        if page_link is not None:
            yield response.follow(
                page_link,
                meta={"country": response.meta["country"]},
                callback=self.parse,
            )

    def detail(self, response):
        output = {}

        output["ac_installed"] = 0
        output["tpms_installed"] = 0

        # scraping info
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "BeForward"
        output["scraped_listing_id"] = response.url.split("/")[-2]
        output["vehicle_url"] = response.url

        # location details
        output["country"] = response.meta["country"]
        city = response.xpath('//*[@id="spec"]/div[1]/div[2]/span[2]/b/text()').get()
        if check_city(output["country"], city) == False:
            output["city"] = city

        price_field = response.xpath('//span[@class="price ip-usd-price"]/text()').get()
        if price_field is not None:
            # pricing details
            output["price_retail"] = float(
                price_field.replace("$", "").replace(",", "").strip()
            )
            output["currency"] = "USD"

        # basic vehicle info
        output["make"] = response.xpath('//*[@id="bread"]/li[2]/a/text()').get()
        output["model"] = response.xpath('//*[@id="bread"]/li[4]/a/text()').get()

        # vehicle specifications
        table_keys = response.xpath('//table[@class="specification"]//th').getall()
        table_values = response.xpath('//table[@class="specification"]//td').getall()

        for i in range(0, int(len(table_keys) / 2 + 1)):
            key = Selector(text=table_keys[i]).xpath("//text()").get()
            value = Selector(text=table_values[i]).xpath("//text()").get()
            if value is not None and value.strip() != "N/A" and value.strip() != "-":
                key = key.lower()
                value = value.strip()
                if key == "mileage":
                    mileage = int(value.split(" ")[0].replace(",", ""))
                    unit = value.split(" ")[1]
                    output["odometer_value"] = mileage
                    output["odometer_unit"] = unit
                elif key == "chassis no.":
                    output["chassis_number"] = value
                elif key == "steering":
                    output["steering_position"] = value
                elif key == "engine size":
                    value = value.replace(",", "")
                    engine_value = int(re.findall(r"\d*", value)[0])
                    engine_unit = value.replace(str(engine_value), "")
                    output["engine_displacement_value"] = str(engine_value)
                    output["engine_displacement_units"] = engine_unit
                elif key == "ext. color":
                    output["exterior_color"] = value
                elif key == "fuel":
                    output["fuel"] = value
                elif key == "seats":
                    value = value.split(" ")[0]
                    if "(" in value:
                        value = value.split("(")[0]
                    output["seats"] = int(value)
                elif key == "drive":
                    output["drive_train"] = value
                elif key == "doors":
                    value = value.split(" ")[0]
                    output["doors"] = int(value)
                elif key == "transmission":
                    output["transmission"] = value
                elif key == "registration":
                    output["registration_year"] = value.split("/")[0]
                elif key == "manufacture":
                    output["year"] = int(value.split("/")[0])

        # vehicle features - upholstery, ac_installed
        vehicle_features = response.xpath(
            '//div[@class="remarks"]//li[@class="attached_on"]/text()'
        ).getall()
        for i in range(0, int(len(vehicle_features) / 2)):
            value = vehicle_features[i]
            if value == "Leather Seat":
                output["upholstery"] = "leather"
            elif value == "A/C":
                output["ac_installed"] = 1

        # pictures list
        img = response.xpath(
            '//div[@class="list-detail-left list-detail-left-renewal"]/div[@id="gallery"]/ul/li/a/img/@src'
        ).getall()
        for i in range(len(img)):
            img[i] = "https:" + img[i]
        output["picture_list"] = json.dumps(img)

        # process empty fields
        list1 = []
        list2 = []
        for k, v in output.items():
            if v or v == 0:
                list1.append(k)
                list2.append(v)
        output = dict(zip(list1, list2))
        # apify.pushData(output)


def check_city(country_code, city):
    country_full_name = ""
    if country_code == "AE":
        country_full_name = "UAE"
    elif country_code == "SG":
        country_full_name = "SINGAPORE"
    elif country_code == "TH":
        country_full_name = "THAILAND"
    elif country_code == "GB":
        country_full_name = "UNITED KINGDOM"
    elif country_code == "KR":
        country_full_name = "KOREA"
    elif country_code == "JP":
        country_full_name = "JAPAN"

    return city.lower() == country_full_name.lower()
