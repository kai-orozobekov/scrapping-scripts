import json
import scrapy
import datetime
import html
import os

import apify


class Jiji(scrapy.Spider):
    name = "jiji"
    download_timeout = 120
    start_urls = ["https://jiji.ng/api_web/v1/listing?slug=cars&webp=true"]

    def parse(self, response):
        jsn = json.loads(html.unescape(response.body.decode()))
        # Traverse product links
        for v in jsn["adverts_list"]["adverts"]:
            url = (
                response.url.split("/v1")[0]
                + "/v1/item/"
                + v["guid"]
                + "?"
                + v["url"].split("?")[-1]
                + "&webp=true"
            )
            yield scrapy.Request(url=url, callback=self.detail)

        # pagination
        if jsn["next_url"] is not None:
            yield scrapy.Request(url=jsn["next_url"], callback=self.parse)

    def detail(self, response):
        jsn = json.loads(html.unescape(response.body.decode()))
        advert = jsn["advert"]
        header = jsn["header_data"]
        output = {}

        # make, model, year, odometer_value, odometer_unit, engine_displacement_value, engne_displacement_units
        for dict_data in advert["attrs"]:
            if dict_data["name"] == "Make":
                output["make"] = dict_data["value"]

            elif dict_data["name"] == "Model":
                output["model"] = dict_data["value"]

            elif dict_data["name"] == "Year of Manufacture":
                output["year"] = int(dict_data["value"])

            elif dict_data["name"] == "Transmission":
                output["transmission"] = dict_data["value"]

            elif dict_data["name"] == "Mileage":
                output["odometer_value"] = int(dict_data["value"])
                output["odometer_unit"] = dict_data["unit"]

            elif dict_data["name"] == "Engine Size":
                output["engine_displacement_value"] = str(dict_data["value"])
                output["engne_displacement_units"] = dict_data["unit"]

        # ac_installed, tpms_installed, scraped_date, scraped_from, scraped_listing_id, vehicle_url
        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "Jiji"
        output["scraped_listing_id"] = str(advert["id"])
        output["vehicle_url"] = advert["url"]

        # picutre_list, city, country, price_retail, price_wholeslae, currency
        output["picture_list"] = json.dumps([img["url"] for img in advert["images"]])
        output["city"] = advert["region_name"]
        output["country"] = header["current_region_name"]
        output["price_retail"] = float(advert["price"]["value"])
        if output.get("price_retail"):
            output["price_wholesale"] = output["price_retail"]
        output["currency"] = advert["price"]["title"].split(" ")[0]
        if output["currency"] == "₦":
            output["currency"] = "NGN"
        elif output["currency"] == "GH₵":
            output["currency"] = "GHS"

        # yield output
        apify.pushData(output)
