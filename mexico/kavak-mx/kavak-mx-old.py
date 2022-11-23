import json
import scrapy
import datetime
import html
import apify


class Kavak(scrapy.Spider):
    name = "kavak"
    download_timeout = 120
    page = 1
    start_urls = ["https://www.kavak.com/mx/page-1/compra-de-autos"]

    def parse(self, response):
        self.page += 1
        url = response.url

        # traverse vehicle links
        product_links = response.xpath("//a[@class='card-inner']/@href").getall()
        for link in product_links:
            if link.split("-")[-1]:
                href = (
                    "https://api.kavak.services/services-common/inventory/"
                    + link.split("-")[-1]
                    + "/static"
                )
                yield response.follow(
                    href,
                    callback=self.detail,
                    cb_kwargs={"country": url.split("/")[-3]},
                )

        if (
            self.page
            < int(response.xpath("//div[@class='results']/span[3]/text()").get()) + 1
        ):
            next_page = url.replace(f"page-{self.page-1}", f"page-{self.page}")
            yield response.follow(next_page, callback=self.parse)

    def detail(self, response, country):
        output = {}

        # country map
        ctry_map = {
            "mx": "Mexico",
            "br": "Brazil",
            "ar": "Argentina",
            "tr": "Turkey",
            "co": "Colombia",
            "cl": "Chile",
            "pe": "Peru",
        }

        # currency codes map
        curr_map = {
            "mx": "MXN",
            "br": "BRL",
            "ar": "ARS",
            "tr": "TRL",
            "co": "COP",
            "cl": "CLP",
            "pe": "PEN",
        }
        jsn = json.loads(html.unescape(response.body.decode()))
        output["ac_installed"] = 0

        data = jsn["data"]
        if data["exteriorColor"] is not None:
            output["exterior_color"] = data["exteriorColor"]
        if data["bodyType"] is not None:
            output["body_type"] = data["bodyType"]

        for feature in data["features"]["mainAccessories"]["items"]:
            if feature["name"] == "Litros":
                output["engine_displacement_value"] = feature["value"]
                output["engine_displacement_units"] = "L"

        for feature in data["features"]["otherAccessories"]:
            if feature["name"] == "Exterior":
                for category in feature["categories"]:
                    if category["name"] == "Puertas":
                        output["doors"] = int(category["items"][0]["value"])
            if feature["name"] == "Equipamiento":
                for category in feature["categories"]:
                    if category["name"] == "Aire":
                        if category["items"][0]["value"] == "Aire Acondicionado":
                            output["ac_installed"] = 1
            if feature["name"] == "Interior":
                for category in feature["categories"]:
                    if category["name"] == "Asientos":
                        output["upholstery"] = category["items"][0]["value"]
                    if category["name"] == "Pasajeros":
                        output["seats"] = int(category["items"][0]["value"])

        output["make"] = data["make"]
        output["model"] = data["model"]
        output["year"] = int(data["carYear"])
        output["trim"] = data["trim"]
        output["transmission"] = data["transmission"]
        output["tpms_installed"] = 0
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "Kavak"
        output["scraped_listing_id"] = str(data["id"])
        output["odometer_value"] = int(data["km"])
        if output.get("odometer_value"):
            output["odometer_unit"] = "km"
        output["vehicle_url"] = "https://www.kavak.com/" + country + data["carUrl"]

        medias = [media["media"] for media in data["media"]["inventoryMedia"]]
        medias.extend([media["media"] for media in data["media"]["internalDimples"]])
        medias.extend([media["media"] for media in data["media"]["externalDimples"]])
        output["picture_list"] = json.dumps(
            ["https://images.kavak.services/" + media for media in medias]
        )

        output["city"] = data["region"]["name"]
        output["country"] = ctry_map[country]
        output["price_retail"] = float(data["price"])
        output["currency"] = curr_map[country]

        apify.pushData(output)
