import scrapy
import os
import json
import datetime
import html

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
        output["price_wholesale"] = output["price_retail"]
        output["currency"] = "NGN"
        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "Otutu"
        output["scraped_listing_id"] = response.url.split("/")[-2]
        output["vehicle_url"] = response.url
        output["picture_list"] = json.dumps(
            response.xpath("//a[@data-fancybox='group']/@href").getall()
        )
        output["country"] = "Nigeria"

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
                output["price_wholesale"] = output["price_retail"]
                output["currency"] = "NGN"

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
                output["city"] = des_value[i]

            elif des_key[i] == "Fuel Type":
                output["fule"] = des_value[i]

        # description points
        des_data = response.xpath("//div[@class='desc-points']/p")
        for data in des_data:
            k = "".join(data.xpath("./text()").getall())
            v = "".join(data.xpath("./span/text()").getall())
            if k == "" and len(data.xpath("./span")) == 2:
                k = "".join(data.xpath("./span[1]/text()").getall())
                v = "".join(data.xpath("./span[2]/text()").getall())

            if "Make" in k:
                output["make"] = v

            elif "Model" in k:
                output["model"] = v

            elif "Year of manufacture" in k:
                output["year"] = v

            elif "Transmission" in k:
                output["transmission"] = v

            elif "Mileage" in k:
                odometer = v.replace("km", "").strip()
                if odometer:
                    output["odometer_value"] = int(
                        v.replace("km", "").replace("k", "").replace(",", "").strip()
                    )
                    output["odometer_unit"] = "km"

            elif "Trim" in k:
                output["trim"] = v

        # process empty fields
        list1 = []
        list2 = []
        for k, v in output.items():
            if v or v == 0:
                list1.append(k)
                list2.append(v)
        output = dict(zip(list1, list2))

        # yield output
        # apify.pushData(output)
