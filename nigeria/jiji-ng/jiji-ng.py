import json
import scrapy
import datetime
import html

# import apify


class Jiji(scrapy.Spider):
    name = "jiji"
    download_timeout = 120
    # remove on apify
    custom_settings = {
        "CONCURRENT_REQUESTS": 5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 5,
        "DOWNLOAD_DELAY": 0.25,
    }
    # ---
    start_urls = ["https://jiji.ng/api_web/v1/listing?slug=cars&webp=true"]

    def parse(self, response):
        jsn = json.loads(html.unescape(response.body.decode()))
        # Traverse product links
        for listing in jsn["adverts_list"]["adverts"]:
            if "guid" in listing:
                url = response.url.split("/v1")[0] + "/v1/item/" + listing["guid"]
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

            elif dict_data["name"] == "Trim":
                output["trim"] = dict_data["value"]

            elif dict_data["name"] == "Body":
                output["body_type"] = dict_data["value"]

            elif dict_data["name"] == "Fuel":
                output["fuel"] = dict_data["value"]

            elif dict_data["name"] == "Drivetrain":
                output["drive_train"] = dict_data["value"]

            elif dict_data["name"] == "Number of Cylinders":
                output["engine_cylinders"] = int(dict_data["value"])

            elif dict_data["name"] == "Color":
                output["exterior_color"] = dict_data["value"]

            elif dict_data["name"] == "VIN Chassis number":
                output["vin"] = dict_data["value"]

            elif dict_data["name"] == "Seats":
                output["seats"] = int(dict_data["value"])

            elif dict_data["name"] == "Engine Size":
                output["engine_displacement_value"] = dict_data["value"]
                output["engine_displacement_units"] = dict_data["unit"]

            elif dict_data["name"] == "Mileage":
                output["odometer_value"] = int(dict_data["value"])
                output["odometer_unit"] = dict_data["unit"]

            elif dict_data["name"] == "Condition":
                value = dict_data["value"]
                if "used" in value.lower():
                    output["is_used"] = 1

            elif dict_data["name"] == "Engine Size":
                output["engine_displacement_value"] = str(dict_data["value"])
                output["engne_displacement_units"] = dict_data["unit"]

        output["ac_installed"] = 0
        output["tpms_installed"] = 0

        # scrapping info
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "Jiji"
        output["scraped_listing_id"] = str(advert["id"])
        output["vehicle_url"] = advert["url"]

        # picutre_list
        output["picture_list"] = json.dumps([img["url"] for img in advert["images"]])

        # location
        output["city"] = advert["region_name"]
        output["state_or_province"] = advert["region_text"]
        output["country"] = header["current_region_name"]

        # pricing
        output["price_retail"] = float(advert["price"]["value"])
        output["currency"] = advert["price"]["title"].split(" ")[0]
        if output["currency"] == "₦":
            output["currency"] = "NGN"
        elif output["currency"] == "GH₵":
            output["currency"] = "GHS"

        output["vehicle_disclosure"] = advert["description"]
        # apify.pushData(output)
