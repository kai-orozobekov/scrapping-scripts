import json
import scrapy
import datetime
from scrapy import Selector

# import apify


class SbtjapanSpider(scrapy.Spider):
    name = "sbtjapan"
    download_timeout = 120
    start_urls = [
        "https://www.sbtjapan.com/used-cars/?custom_search=japan_inventory&location=ujapan&p_num=1#listbox"
    ]

    def parse(self, response):
        tree = Selector(response)
        carlist = tree.xpath("//li[@class='car_listitem']")
        link_list = [i.xpath(".//h2/a/@href").extract_first() for i in carlist]
        yield from response.follow_all(link_list, self.product_detail)

        next_link = tree.xpath('//a[@id="page_next"]/@href').extract_first()
        if next_link:
            yield response.follow(next_link, self.parse)

    def product_detail(self, response):
        output = {}
        tree = Selector(response)

        output["make"] = tree.xpath(
            "//li[@itemprop='itemListElement'][3]/a/span/text()"
        ).extract_first()
        output["model"] = tree.xpath(
            "//li[@itemprop='itemListElement'][4]/a/span/text()"
        ).extract_first()

        form_data_th = tree.xpath(
            "//div[@class='carDetails']/table[1]//tr/th/text()"
        ).extract()
        form_data_td = tree.xpath(
            "//div[@class='carDetails']/table[1]//tr/td/text()"
        ).extract()

        form_data_th.remove("Model Year:")

        print(form_data_th)

        # parse form data
        for i in range(len(form_data_th)):
            key = form_data_th[i].lower().replace(":", "")
            value = form_data_td[i].strip()
            if "registration year" == key:
                output["registration_year"] = value
            elif "transmission" == key:
                output["transmission"] = value
            elif "fuel" == key:
                output["fuel"] = value
            elif "color" == key:
                output["exterior_color"] = value
            elif "drive" == key:
                output["drive_train"] = value
            elif "door" == key:
                output["doors"] = int(value)
            elif "seating capacity" == key:
                output["seats"] = int(value)
            elif "steering" == key:
                output["steering_position"] = value
            elif "body type" == key:
                output["body_type"] = value
            elif "engine size" == key:
                value = value.replace(",", "")
                output["engine_displacement_value"] = "".join(
                    [i for i in list(value) if i.isdigit()]
                )
                output["engine_displacement_units"] = "".join(
                    [i for i in list(value) if i.isalpha()]
                )

            elif "stock id" == key:
                output["scraped_listing_id"] = value
            elif "mileage" == key:
                # Mileage value and unit are connected and need to be taken out circularly
                output["odometer_value"] = int(
                    "".join([i for i in list(value) if i.isdigit() or i == "."])
                )
                output["odometer_unit"] = "".join(
                    [i for i in list(value) if i.isalpha()]
                )
            elif "inventory location" == key:
                # location may be null,may be have "country" and "state_or_province" may be only "country"
                if value and "-" in value:
                    output["state_or_province"] = value.split("-")[0].strip()
                    output["country"] = value.split("-")[1].strip()
                elif "-" not in value:
                    output["country"] = value.strip()

        output["ac_installed"] = 0
        output["tpms_installed"] = 0

        # scraping info
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "sbtjapan"
        output["vehicle_url"] = response.url

        # pictures list
        picture_list = tree.xpath(
            "//div[@id='car_thumbnail_car_navigation']//img/@data-lazy"
        ).extract()
        # Loop to enlarge the small picture
        if picture_list:
            output["picture_list"] = json.dumps(
                [i.split("=")[0] + "=640" for i in picture_list]
            )

        # price may be null
        price = tree.xpath(
            '//table[@class="calculate "]//span[@id="fob"]/text()'
        ).extract_first()
        if price and "ask" not in price.lower():
            price_value = price.strip().split(" ")
            output["price_retail"] = float(price_value[1].replace(",", ""))
            output["currency"] = price_value[0]

        # accessories table
        included_accessories = form_data_th = tree.xpath(
            "//table[@class='accesories']//tr/td[not(@class)]/text()"
        ).extract()

        for accessory in included_accessories:
            value = accessory.strip().lower()
            if value == "air conditioner":
                output["ac_installed"] = 1
            elif value == "leather seats":
                output["upholstery"] = "leather"

        # process empty fields
        list1 = []
        list2 = []
        for k, v in output.items():
            if v or v == 0:
                list1.append(k)
                list2.append(v)
        output = dict(zip(list1, list2))

        # apify.pushData(output)
