import re
import json
import scrapy
import datetime
from scrapy import Selector


class CarrosSpider(scrapy.Spider):
    name = "carros"
    download_timeout = 120
    start_urls = [
        "https://carros.com/automobiles-for-sale/dominican-republic-co219/?page=1"
    ]

    def parse(self, response):
        tree = Selector(response)  # create Selector
        data_list = tree.xpath(
            '//div[contains(@class, "post-item-wrapper relative")]/a/@href'
        ).extract()
        link_list = ["https://carros.com" + i for i in data_list]  # detail url list

        yield from response.follow_all(link_list, self.product_detail)

        current_page = int(str(response.url).split("page=")[1])
        number_list = tree.xpath(
            '//div[@class="flex flex-center hs-pagination"][1]/span/text()'
        ).extract_first()  # page number
        if (
            number_list
        ):  # There is no page number on the last page, which needs to be judged
            last_number = number_list.split("/")[1]  # get last page number
        else:
            last_number = current_page
        pagination_links = [
            response.url.split("page=")[0] + f"page={i}"
            for i in range(int(current_page) + 1, int(last_number) + 1)
        ]  # all page link
        if int(current_page) + 1 < int(last_number) + 1:
            yield from response.follow_all(pagination_links, self.parse)

    def product_detail(self, response):
        output = {}
        tree = Selector(response)  # create Selector

        # get picture list
        pictures = tree.xpath("//div[@class='slider-thumbnail-item']/@style").extract()
        picture_list = []
        for p in pictures:
            picture = re.findall("url\((.*?)\)", p, re.S)[0]
            if "https://carros.com" not in picture:
                picture = "https://carros.com" + picture
            picture_list.append(picture)
        # Some web pages only have one picture,Need separate parsing
        if not picture_list:
            picture_list = tree.xpath(
                '//div[@class="slider-item active"]/img/@src'
            ).extract()

        for i in tree.xpath("//div[@class='detail-item']"):
            label_key = i.xpath("./label/text()").extract()[0].strip().lower()
            value = i.xpath("./b/text()").extract()[0].strip().lower()
            if label_key == "condition":
                if value == "used":
                    output["is_used"] = 1
            elif label_key == "manufacturer":
                output["make"] = value
            elif label_key == "model":
                output["model"] = value
            elif label_key == "year":
                output["year"] = int(value)
            elif label_key == "transmission":
                output["transmission"] = value
            elif label_key == "mileage":
                data = value.split(" ")
                output["odometer_value"] = int(data[0])
                output["odometer_unit"] = data[1]
            elif label_key == "car body style":
                output["body_type"] = value
            elif label_key == "cylinders":
                output["engine_cylinders"] = int(value.split(" ")[0])
            elif label_key == "fuel type":
                output["fuel"] = value
            elif label_key == "vin":
                if len(value) > 5:
                    output["vin"] = value
            elif label_key == "price":
                data = value.split(" ")
                output["price_retail"] = float(
                    data[0 if len(data) == 2 else 1].replace(",", "")
                )
                output["price_wholesale"] = output["price_retail"]
                output["currency"] = data[0 if len(data) == 2 else 1]

        output["ac_installed"] = 0
        # check if there is "Comfort" panel on the page that contains information about air-conditioning
        for i in tree.xpath(
            "//div[contains(@class, 'panel') and contains(@class, 'panel-default')]"
        ):
            title = (
                i.xpath(
                    "./div[contains(@class, 'panel-heading')]/div[contains(@class, 'panel-title')]/a/text()"
                )
                .extract()[0]
                .strip()
                .lower()
            )
            if title == "comfort":
                details_list = i.xpath(
                    "./div[contains(@class, 'panel-collapse')]/div[contains(@class, 'panel-body')]/div[contains(@class, 'row')]/div/label/div/span/text()"
                ).extract()
                for detail in details_list:
                    if detail.lower() == "air-conditioning":
                        output["ac_installed"] = 1

        output["tpms_installed"] = 0
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "carros.com"
        output["scraped_listing_id"] = re.findall("-p(.*?)/", response.url, re.S)[0]
        output["country"] = "Dominican Republic"
        output["vehicle_url"] = response.url
        output["picture_list"] = json.dumps(picture_list)
        output["vehicle_disclosure"] = tree.xpath(
            "//div[contains(@class, 'description-box')]/text()"
        ).extract()[0]

        location = (
            tree.xpath("//div[contains(@class, 'post-location')]/text()")
            .extract()[1]
            .strip()
        )
        if location:
            location_details = location.split(",")
            # at maximum we can get 3 items in a list
            # first - province, second - city, third - postal code
            # if we get 2 items in a list, then first item - province, second item - city OR postal code
            # thus, needs to be checked
            output["state_or_province"] = location_details[0]
            if len(location_details) > 1:
                city = location_details[1].strip()
                if city != "other" and city.isnumeric() == False:
                    output["city"] = city

        # process empty fields
        list1 = []
        list2 = []
        for k, v in output.items():
            if v or v == 0:
                list1.append(k)
                list2.append(v)
        output = dict(zip(list1, list2))

        # apify.pushData(output)
        print(output)
