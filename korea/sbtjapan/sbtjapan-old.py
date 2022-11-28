import scrapy
import os
import json
import datetime
from scrapy import Selector

# import apify


class SbtjapanSpider(scrapy.Spider):
    name = "sbtjapan"
    download_timeout = 120
    start_urls = [
        "https://www.sbtjapan.com/used-cars/?custom_search=korea_inventory&location=korea&p_num=1#listbox"
    ]

    def parse(self, response):
        tree = Selector(response)  # create Selector
        carlist = tree.xpath("//li[@class='car_listitem']")
        link_list = [
            i.xpath(".//h2/a/@href").extract_first() for i in carlist
        ]  # link list
        yield from response.follow_all(link_list, self.product_detail)

        next_link = tree.xpath('//a[@id="page_next"]/@href').extract_first()
        if next_link:
            yield response.follow(next_link, self.parse)

    def product_detail(self, response):
        output = {}
        tree = Selector(response)  # create Selector

        output["make"] = tree.xpath(
            "//li[@itemprop='itemListElement'][3]/a/span/text()"
        ).extract_first()
        output["model"] = tree.xpath(
            "//li[@itemprop='itemListElement'][4]/a/span/text()"
        ).extract_first()

        form_data_th = tree.xpath(
            "//div[@class='carDetails']/table[1]//tr/th/text()"
        ).extract()
        form_data_td = tree.xpath("//div[@class='carDetails']/table[1]//tr/td")
        for i in range(len(form_data_th)):  # parse form data
            key = form_data_th[i]
            value = form_data_td[i]
            if "chassis" in key.lower():
                output["vin"] = value.xpath("./text()").extract_first()
            elif "year" in key.lower():
                output["year"] = value.xpath("./text()").extract_first()
                if output["year"]:  # May be null,need to judge
                    output["year"] = int(output["year"].split("/")[0])
            elif "transmission" in key.lower():
                output["transmission"] = value.xpath("./text()").extract_first()
            elif "fuel" in key.lower():
                output["fuel"] = value.xpath("./text()").extract_first()
            elif "mileage" in key.lower():
                # Mileage value and unit are connected and need to be taken out circularly
                output["odometer_value"] = int(
                    "".join(
                        [
                            i
                            for i in list(value.xpath("./text()").extract_first())
                            if i.isdigit() or i == "."
                        ]
                    )
                )
                output["odometer_unit"] = "".join(
                    [
                        i
                        for i in list(value.xpath("./text()").extract_first())
                        if i.isalpha()
                    ]
                )
            elif "location" in key.lower():
                # location may be null,may be have "country" and "city" may be only "country"
                location = value.xpath("./text()").extract_first()
                if location and "-" in location:
                    output["city"] = location.split("-")[0].strip()
                    country = location.split("-")[1].strip()
                    if country == "Korea":
                        output["country"] = "KR"
                elif "-" not in location:
                    if location.strip() == "Korea":
                        output["country"] = "KR"

        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "sbtJapan"
        output["scraped_listing_id"] = response.url.split("/")[-2]
        output["vehicle_url"] = response.url

        # price may be null
        price = tree.xpath(
            '//table[@class="calculate "]//span[@id="fob"]/text()'
        ).extract_first()
        if price and "ask" not in price.lower():
            output["price_retail"] = float(price.strip().split(" ")[1].replace(",", ""))
            output["price_wholesale"] = float(
                price.strip().split(" ")[1].replace(",", "")
            )
            output["currency"] = price.strip().split(" ")[0]

        picture_list = tree.xpath(
            "//div[@id='car_thumbnail_car_navigation']//img/@data-lazy"
        ).extract()
        if picture_list:
            output["picture_list"] = json.dumps(
                [i.split("=")[0] + "=640" for i in picture_list]
            )  # Loop to enlarge the small picture

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
