import scrapy
import json
import datetime
import re

# import apify


class AutotraderSpider(scrapy.Spider):
    name = "autotrader"
    download_timeout = 120
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
    start_urls = [
        "https://www.autotrader.ca/cars/?rcp=15&rcs=0&srt=35&prx=-1&hprc=True&wcp=True&iosp=True&sts=Used&inMarket=advancedSearch",
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, cb_kwargs={"page": 1})

    def parse(self, response, page):
        product_links = response.xpath(
            '//div[@id="SearchListings"]/div/div[2]/div[2]/div/div/h2/a/@href'
        ).getall()
        yield from response.follow_all(product_links, self.product_detail)

        if product_links:
            page += 1
            rcp = (page - 1) * 15
            page_link = f"https://www.autotrader.ca/cars/?rcp=15&rcs={rcp}&srt=35&prx=-1&hprc=True&wcp=True&iosp=True&sts=Used&inMarket=advancedSearch"
            yield response.follow(
                url=page_link, callback=self.parse, cb_kwargs={"page": page}
            )

    def product_detail(self, response):
        ex = "window\['ngVdpModel']\ = (.*?)window\['ngVdpGtm'\]"
        jsn = re.findall(ex, response.text, re.S)[0]
        # Re-parsing JSON of product details
        jsn = jsn[::-1].replace(";", "", 1)[::-1].strip()
        jsn = json.loads(jsn)

        output = {}
        print(jsn)

        specs = jsn["specifications"].get("specs")
        for data in specs:
            if data["key"] == "Transmission":
                output["transmission"] = data["value"]
            if data["key"] == "Fuel Type":
                output["fuel"] = data["value"]
            if data["key"] == "Cylinder":
                output["engine_cylinders"] = int(data["value"])
            if data["key"] == "Interior Colour":
                output["interior_color"] = data["value"]
            if data["key"] == "Exterior Colour":
                output["exterior_color"] = data["value"]
            if data["key"] == "Doors":
                output["doors"] = int(data["value"].split(" ")[0])
            if data["key"] == "Passengers":
                output["seats"] = int(data["value"])
            if data["key"] == "Body Type":
                output["body_type"] = data["value"]
            if data["key"] == "Trim":
                output["trim"] = data["value"]
            if data["key"] == "Engine":
                value = data["value"]
                contains_engine_value = re.search(
                    "([+-]?(?=\.\d|\d)(?:\d+)?(?:\.?\d*))(?:[eE]([+-]?\d+))?L", value
                )
                if contains_engine_value:
                    output["engine_displacement_value"] = contains_engine_value.group(1)
                    output["engine_displacement_units"] = "L"
                    block_type = value.replace(
                        f"{contains_engine_value.group(1)}L", ""
                    ).strip()
                    if len(block_type) > 0:
                        output["engine_block_type"] = block_type
                else:
                    output["engine_block_type"] = value
            if data["key"] == "Status":
                if data["value"].lower() == "used":
                    output["is_used"] = 1
            if data["key"] == "Drivetrain":
                output["drive_train"] = data["value"]
            if data["key"] == "Kilometres":
                value = data["value"].split(" ")
                output["odometer_value"] = int(value[0].replace(",", ""))
                output["odometer_unit"] = value[1]

        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        options = jsn["featureHighlights"].get("options")
        if options is not None:
            for option in options:
                if option.lower() == "air conditioning":
                    output["ac_installed"] = 1
                if option.lower() == "leather interior":
                    output["upholstery"] = "leather"

        picture_list_items = jsn["gallery"].get("items")  # picture list
        picture_list = [
            picture.get("photoViewerUrl")
            for picture in picture_list_items
            if picture.get("type") == "Photo"
        ]
        output["picture_list"] = json.dumps(picture_list)

        output["city"] = jsn["deepLinkSavedSearch"]["savedSearchCriteria"].get("city")
        output["state_or_province"] = jsn["deepLinkSavedSearch"][
            "savedSearchCriteria"
        ].get("provinceAbbreviation")
        output["country"] = "Canada"

        output["scraped_from"] = "AutoTrader"
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_listing_id"] = str(jsn["adBasicInfo"].get("adId"))
        output["vehicle_url"] = response.url

        output["price_retail"] = float(jsn["hero"].get("price").replace(",", ""))
        price_mark = jsn["adBasicInfo"].get("price")
        if "$" in price_mark:
            output["currency"] = "USD"

        output["vin"] = jsn["hero"].get("vin")
        output["make"] = jsn["hero"].get("make")
        output["model"] = jsn["hero"].get("model")
        output["year"] = int(jsn["hero"].get("year"))

        description = jsn["description"].get("description")
        if len(description) > 0:
            output["vehicle_disclosure"] = description[0].get("description")

        if "dealerTrust" in jsn:
            dealer_name = jsn["dealerTrust"].get("dealerCompanyName")
            if dealer_name is not None:
                output["dealer_name"] = dealer_name

        dealer_id = jsn["dealerId"]
        if dealer_id is not None:
            output["dealer_id"] = dealer_id

        list1 = []
        list2 = []
        for k, v in output.items():
            if v is not None:
                list1.append(k)
                list2.append(v)
        output = dict(zip(list1, list2))

        # apify.pushData(output)
