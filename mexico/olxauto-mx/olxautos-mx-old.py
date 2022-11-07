import json
import scrapy
import datetime
import html
from urllib.parse import urlencode

# import apify


class OlxAutos(scrapy.Spider):
    name = "olx"
    download_timeout = 120
    page = 0
    url = "https://www.olxautos.com.mx/api/relevance/v2/search?"
    params = {
        "category": "84",
        "facet_limit": "100",
        "location": "1000001",
        "location_facet_limit": "20",
        "page": None,
        "platform": "web-desktop",
        "size": "40",
        "user": "18199604c02x5228328e",
    }

    def start_requests(self):
        self.params["page"] = self.page
        yield scrapy.Request(self.url + urlencode(self.params), callback=self.parse)

    def parse(self, response):
        self.page += 1
        self.params["page"] = self.page

        try:
            jsn = json.loads(html.unescape(response.body.decode()))
            jsn = jsn["data"]
            for data in jsn:
                output = {}

                # make, model, year, trim, transmission, fuel, odometer_value, odometer_unit, vehicle_url
                for dict_data in data["parameters"]:
                    if dict_data["key"] == "make":
                        output["make"] = dict_data["value_name"]

                    elif dict_data["key"] == "model":
                        output["model"] = dict_data["value_name"]
                        output["vehicle_url"] = dict_data["value"]

                    elif dict_data["key"] == "year":
                        output["year"] = int(dict_data["value_name"])

                    elif dict_data["key"] == "body_type":
                        output["trim"] = dict_data["value_name"]

                    elif dict_data["key"] == "transmission":
                        output["transmission"] = dict_data["value_name"]

                    elif dict_data["key"] == "fuel":
                        output["fuel"] = dict_data["value_name"]

                    elif dict_data["key"] == "km_driven":
                        output["odometer_value"] = int(dict_data["value_name"])
                        output["odometer_unit"] = "km"

                # ac_installed, tpms_installed, scraped_date, scraped_from, scraped_listing_id, vehicle_url
                output["ac_installed"] = 0
                output["tpms_installed"] = 0
                output["scraped_date"] = datetime.datetime.isoformat(
                    datetime.datetime.today()
                )
                output["scraped_from"] = "OLX Autos"
                output["scraped_listing_id"] = str(data["id"])
                if output.get("vehicle_url"):
                    output["vehicle_url"] = (
                        "https://www.olxautos.com.mx/item/"
                        + output["make"]
                        + "-"
                        + output["vehicle_url"]
                        + "-"
                        + output["fuel"]
                        + "-iid-"
                        + output["scraped_listing_id"]
                    )

                # picture_list, city, country
                img = data["images"][0]
                output["picture_list"] = json.dumps([img["url"]])
                output["city"] = data["locations_resolved"]["ADMIN_LEVEL_3_name"]
                output["country"] = data["locations_resolved"]["COUNTRY_name"]

                # price, currency
                output["price_retail"] = float(data["price"]["value"]["raw"])
                output["price_wholesale"] = output["price_retail"]
                output["currency"] = data["price"]["value"]["currency"]["iso_4217"]

                # apify.pushData(output)
                # yield output

            yield scrapy.Request(self.url + urlencode(self.params), callback=self.parse)
        except Exception as e:
            raise scrapy.exceptions.CloseSpider("Finish")
