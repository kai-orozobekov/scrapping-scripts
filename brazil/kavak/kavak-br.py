import json
import scrapy
import datetime
import html

# import apify


class Kavak(scrapy.Spider):
    name = "kavak"
    download_timeout = 120
    page = 1
    start_urls = ["https://www.kavak.com/br/page-1/carros-usados"]

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
            "mx": "MX",
            "br": "BR",
            "ar": "AR",
            "tr": "TR",
            "co": "CO",
            "cl": "CL",
            "pe": "PE",
        }

        # currency codes map
        curr_map = {
            "mx": "MXN",
            "br": "BRL",
            "ar": "ARS",
            "tr": "TRY",
            "co": "COP",
            "cl": "CLP",
            "pe": "PEN",
        }
        jsn = json.loads(html.unescape(response.body.decode()))
        data = jsn["data"]

        # body type, exterior color
        if data["exteriorColor"] is not None:
            output["exterior_color"] = data["exteriorColor"]
        if data["bodyType"] is not None:
            output["body_type"] = data["bodyType"]

        # engine details
        for feature in data["features"]["mainAccessories"]["items"]:
            if feature["name"] == "Litros":
                output["engine_displacement_value"] = feature["value"]
                output["engine_displacement_units"] = "L"

        # vehicle basic information
        output["make"] = data["make"]
        output["model"] = data["model"]
        output["year"] = data["carYear"]
        output["trim"] = data["trim"]
        output["transmission"] = data["transmission"]
        output["tpms_installed"] = 0
        output["ac_installed"] = 0

        # scraping details
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "Kavak"
        output["scraped_listing_id"] = str(data["id"])
        output["vehicle_url"] = "https://www.kavak.com/" + country + data["carUrl"]

        # odometer details
        output["odometer_value"] = int(data["km"])
        if output.get("odometer_value"):
            output["odometer_unit"] = "km"

        # number of doors, seats, upholstery, ac_installed
        other_accessories = data["features"]["otherAccessories"]
        for feature in other_accessories:
            categories = feature["categories"]
            if feature["name"] == "Exterior":
                for category in categories:
                    if category["name"] == "Portas":
                        output["doors"] = int(category["items"][0]["value"])
            if feature["name"] == "Equipamento e Conforto":
                for category in categories:
                    if category["name"] == "Aire":
                        item_dict = category["items"][0]
                        if (
                            item_dict["name"].lower() == "aire acondicionado"
                            and item_dict["value"] == "Sí"
                        ):
                            output["ac_installed"] = 1

            if feature["name"] == "Interior":
                for category in categories:
                    if category["name"] == "Assentos":
                        output["upholstery"] = category["items"][0]["value"]
                    if category["name"] == "Passageiros":
                        output["seats"] = int(category["items"][0]["value"])

        # pictures list
        medias = [media["media"] for media in data["media"]["inventoryMedia"]]
        medias.extend([media["media"] for media in data["media"]["internalDimples"]])
        medias.extend([media["media"] for media in data["media"]["externalDimples"]])
        output["picture_list"] = json.dumps(
            ["https://images.kavak.services/" + media for media in medias]
        )

        # location details
        output["city"] = data["region"]["name"]
        output["country"] = ctry_map[country]

        # price details
        output["price_retail"] = float(data["price"])
        output["currency"] = curr_map[country]

        # apify.pushData(output)


"""
word "equipment" mapping
    equipment_map = {
        "mx": "Equipamiento y Confort",
        "br": "Equipamento e Conforto",
        "ar": "Equipamiento",
        "tr": "TRY",
        "co": "Equipamiento",
        "cl": "CLP",
        "pe": "PEN",
    }

word "seating" mapping
    seating_map = {
        "mx": "Asientos",
        "br": "Assentos",
        "ar": "Equipamiento",
        "tr": "TRY",
        "co": "Equipamiento",
        "cl": "CLP",
        "pe": "PEN",
    }

word "doors" mapping
    doors_map = {
        "mx": "Puertas",
        "br": "Portas",
        "ar": "Equipamiento",
        "tr": "TRY",
        "co": "Equipamiento",
        "cl": "CLP",
        "pe": "PEN",
    }
"""
