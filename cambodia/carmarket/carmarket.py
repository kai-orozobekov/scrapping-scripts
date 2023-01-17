import re
import json

# import apify
import scrapy
import datetime


class CarmarketSpider(scrapy.Spider):
    name = "carmarket"
    start_urls = [
        "https://carmarketkh.com/vehicles?page=1&keyword=&type=&user=&added=&make=&model=&badge=&series=&min_price=&max_price=&body_type=&drive_type=&fuel_type=&fuel_economy=&transmission=&cylinder=&interior_color=&exterior_color=&features=&lifestyle=&min_year=&max_year=&doors=&min_engine_size=&max_engine_size=&min_seats=&max_seats=&address=&city=&latitude=&longitude=&distance=&onsale=&sort_by=1"
    ]

    def parse(self, response):
        jsn_data = response.xpath(
            "//div[@class='car-list-page padd-t-50']/vehicle-component/attribute::*"
        ).get()

        jsn_data = json.loads(jsn_data)

        data_list = jsn_data["data"]
        for data in data_list:
            output = {}
            output["make"] = data["make"]["translations"][0].get("name")
            output["model"] = data["model"]["translations"][0].get("name")
            output["scraped_listing_id"] = data["id"]
            if "city" in data:
                output["city"] = data["city"]
            output["vehicle_disclosure"] = data["translations"][0][
                "description"
            ].replace(
                "\n", ""
            )  ## by NT
            if data["country"] == "Cambodia":
                output["country"] = "KH"
            output["price_retail"] = float(data["price"])
            detail_link = data["slug"]

            yield response.follow(
                "https://carmarketkh.com/vehicle/" + detail_link,
                self.product_detail,
                cb_kwargs=output,
            )

        last_page = int(jsn_data["last_page"])
        current_page = int(re.findall("page=(.*?)&", response.url, re.S)[0])
        print(last_page, " ", current_page)

        if current_page < last_page + 1:
            yield response.follow(
                response.url.replace(f"page={current_page}", f"page={current_page+1}"),
                self.parse,
            )

    def product_detail(self, response, **kwargs):
        output = kwargs
        output["ac_installed"] = 0
        form_data = response.xpath(
            '//div[@id="collapse-A"]//ul/li  | //div[@id="collapse-B"]//ul/li| //div[@id="collapse-C"]//ul/li'
        )
        for data in form_data:
            key = data.xpath("./div[1]/text()").get()
            value = data.xpath("./div[2]/text()").get()
            if "Build Date" in key:
                output["year"] = int(
                    "".join([i for i in list(value) if i.isdigit()])
                )  # 'July/1998'
            elif "Transmission" in key:
                output["transmission"] = value.strip()
            elif "Engine" in key:
                output["engine_displacement_value"] = value.strip().split(" ")[0]
                output["engine_displacement_units"] = value.strip().split(" ")[1]
            elif "Fuel Type" in key:
                output["fuel"] = value.strip()
            elif "Kilometers" in key:
                odometer_value = int(
                    "".join([i for i in list(value.strip()) if i.isdigit()])
                )
                if odometer_value:
                    output["odometer_value"] = int(odometer_value)
                    output["odometer_unit"] = "".join(
                        [i for i in list(value.strip()) if i.isalpha()]
                    )
            elif "Body" in key:  ## by NT
                output["body_type"] = value.strip()  ## by NT
            elif "Exterior Colour" in key:  ## by NT
                output["exterior_color"] = value.strip()  ## by NT
            elif "Interior colour" in key:  ## by NT
                output["interior_color"] = value.strip()  ## by NT
            elif "Air Condition" in key:  ## by NT
                output["ac_installed"] = 1  ## by NT
            elif "Drive Type" in key:  ## by NT
                output["drive_train "] = value.strip()  ## by NT
            elif "Doors" in key:  ## by NT
                output["doors"] = value.strip()  ## by NT
            elif "Seats" in key:  ## by NT
                output["seats"] = value.strip()  ## by NT
            elif "Cylinders" in key:  ## by NT
                output["engine_cylinders"] = value.strip()  ## by NT

        output["tpms_installed"] = 0
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "carmarketkh"
        output["vehicle_url"] = response.url

        currency = response.xpath('//div[@class="govt-charges"]/strong/text()').get()
        if "$" in currency:
            output["currency"] = "USD"

        picture_list = response.xpath("//vehicle-images-component/attribute::*").get()
        if picture_list:
            picture_list = eval(picture_list.replace("null", "None"))
            output["picture_list"] = json.dumps(
                [
                    "https://carmarket.com.kh/timthumb.php?src="
                    + i["image_full_path"].replace("\\", "")
                    + "&w=910&h=468&zc=0"
                    for i in picture_list
                ]
            )

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
