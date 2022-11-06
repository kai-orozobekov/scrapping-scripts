import scrapy
import json
import datetime
import re

# import apify


class Otutu(scrapy.Spider):
    name = "otutu"
    download_timeout = 120
    start_urls = ["https://otutu.com.ng/search-results/?cat_id=298"]

    def parse(self, response):
        # Traverse product links
        product_links = response.xpath(
            "//h2[@class='great-product-heading']/a/@href"
        ).getall()
        prices = response.xpath("//h4[@class='sb-list-2-price']/text()").getall()
        for link, price in zip(product_links, prices):
            yield response.follow(
                link, callback=self.detail, cb_kwargs={"price": price}
            )

        # pagination
        page_name = response.xpath(
            "//ul[@class='pagination pagination-lg']/li/a/text()"
        ).getall()
        page_link = response.xpath(
            "//ul[@class='pagination pagination-lg']/li/a/@href"
        ).getall()
        for i in range(len(page_name)):
            if page_name[i] == "Next Page »":
                yield response.follow(page_link[i], self.parse)

    def detail(self, response, price):
        output = {}

        output["price_retail"] = float(price.replace("₦", "").replace(",", ""))
        output["currency"] = "NGN"
        output["country"] = "Nigeria"
        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "Otutu"
        output["scraped_listing_id"] = response.url.split("/")[-2]
        output["vehicle_url"] = response.url
        output["picture_list"] = json.dumps(
            response.xpath("//a[@data-fancybox='group']/@href").getall()
        )

        # description head
        des_key = response.xpath(
            "//div[@class='clear-custom row']/div/span/strong/text()"
        ).getall()
        des_key = [v.strip() for v in des_key if v.strip() != "Colour"]
        des_value = response.xpath(
            "//div[@class='clear-custom row']/div/text()"
        ).getall()
        des_value = [v.replace("\n", "") for v in des_value if v != "\n"]

        for i in range(len(des_key)):
            if des_key[i].strip() == "Price":
                output["price_retail"] = float(
                    des_value[i].replace("₦", "").replace(",", "")
                )

            elif des_key[i] == "Vehicle Name":
                output["make"] = des_value[i]

            elif des_key[i] == "Model":
                output["model"] = des_value[i]

            elif des_key[i] == "Model Year":
                output["year"] = int(des_value[i])

            elif des_key[i] == "Mileage":
                output["odometer_value"] = int(
                    des_value[i]
                    .replace("up to", "")
                    .replace(",", "")
                    .replace("miles", "")
                    .strip()
                )
                output["odometer_unit"] = des_value[i].split(" ")[-1]

            elif des_key[i] == "Gear Box Transmission":
                output["transmission"] = des_value[i]

            elif des_key[i] == "Location":
                output["city"] = (
                    des_value[i].replace("Nigeria", "").replace(",", "").strip()
                )

            elif des_key[i] == "Fuel Type":
                output["fuel"] = des_value[i]

            elif des_key[i] == "Doors":
                output["doors"] = int(des_value[i])

            elif des_key[i] == "Body Type / Style":
                output["body_type"] = des_value[i]

            elif des_key[i] == "Comfort Features":
                features = [element.strip() for element in des_value[i].split(",")]
                if "Air-Conditioning" in features:
                    output["ac_installed"] = 1
                if "4 Wheel Drive" in features:
                    output["drive_train"] = "4 Wheel Drive"
                if "Leather Seat" in features:
                    output["upholstery"] = "Leather"

            elif des_key[i] == "Condition":
                condition = des_value[i]
                if "used" in condition.lower():
                    output["is_used"] = 1

        output["vehicle_disclosure"] = "\n".join(
            response.xpath("//div[@class='desc-points']/p/text()").getall()
        )

        description_list = list(
            element.strip()
            for element in response.xpath(
                "//div[@class='desc-points']/p//text()"
            ).getall()
        )

        for element in description_list:
            if "mileage" in element.lower() and "odometer_value" not in output:
                value = re.findall(r"\d+", element.replace(",", ""))
                if len(value) > 0 and value[0].isnumeric():
                    contains_k = re.search(
                        "([+-]?(?=\.\d|\d)(?:\d+)?(?:\.?\d*))(?:[eE]([+-]?\d+))?k$",
                        element,
                    )
                    if contains_k:
                        output["odometer_value"] = int(value[0]) * 1000
                        output["odometer_unit"] = "km"
                    if "km" in element.lower():
                        output["odometer_value"] = int(value[0])
                        output["odometer_unit"] = "km"
                    if "miles" in element.lower():
                        output["odometer_value"] = int(value[0])
                        output["odometer_unit"] = "miles"
                    check = (
                        element.replace(",", "")
                        .replace(value[0], "")
                        .replace("Mileage", "")
                        .replace(":", "")
                    )
                    if len(check.strip()) == 0:
                        output["odometer_value"] = int(value[0])
                        output["odometer_unit"] = "km"
            if "body" in element.lower() and "body_type" not in output:
                value = (
                    element.lower()
                    .replace("body", "")
                    .replace("type", "")
                    .replace("style", "")
                    .replace(":", "")
                )
                if len(value.strip()) > 0:
                    output["body_type"] = value.strip()
            if "colour" in element.lower():
                value = element.lower().replace("colour", "").replace(":", "").strip()
                if len(value) > 0:
                    color_array = list(filter(lambda v: len(v) > 0, value.split(" ")))
                    if len(color_array) < 3:
                        if "exterior" in color_array:
                            output["exterior_color"] = color_array[1]
                        if "interior" in color_array:
                            output["interior_color"] = color_array[1]
                        if (
                            len(color_array) == 2
                            and "exterior" not in color_array
                            and "interior" not in color_array
                        ):
                            output["exterior_color"] = " ".join(color_array)
                        if len(color_array) == 1:
                            output["exterior_color"] = color_array[0]
            print(element)

        # process empty fields
        list1 = []
        list2 = []
        for k, v in output.items():
            if v or v == 0:
                list1.append(k)
                list2.append(v)
        output = dict(zip(list1, list2))

        # print(output)
        # apify.pushData(output)
