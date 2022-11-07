import scrapy
import os
import json
import re
import math
import datetime

# import apify


class OlistSpider(scrapy.Spider):
    name = "olist"
    download_timeout = 120

    start_urls = [
        "https://olist.ng/api/item/search?page=1&size=10&subcat_name=cars&title=Toyota%20Cars%20in%20Nigeria&make=11092&make_t=Toyota&cityName=&city=Nigeria",
        "https://olist.ng/api/item/search?page=1&size=10&subcat_name=cars&title=Honda%20Cars%20in%20Nigeria&make=11093&make_t=Honda&cityName=&city=Nigeria",
        "https://olist.ng/api/item/search?page=1&size=10&subcat_name=cars&title=Nissan%20Cars%20in%20Nigeria&make=11094&make_t=Nissan&cityName=&city=Nigeria",
        "https://olist.ng/api/item/search?page=1&size=10&subcat_name=cars&title=Mercedes-Benz%20Cars%20in%20Nigeria&make=11095&make_t=Mercedes-Benz&cityName=&city=Nigeria",
        "https://olist.ng/api/item/search?page=1&size=10&subcat_name=cars&title=Volkswagen%20Cars%20in%20Nigeria&make=11096&make_t=Volkswagen&cityName=&city=Nigeria",
        "https://olist.ng/api/item/search?page=1&size=10&subcat_name=cars&title=Infiniti%20Cars%20in%20Nigeria&make=11097&make_t=Infiniti&cityName=&city=Nigeria",
        "https://olist.ng/api/item/search?page=1&size=10&subcat_name=cars&title=Land%20Rover%20Cars%20in%20Nigeria&make=11099&make_t=Land%20Rover&cityName=&city=Nigeria",
        "https://olist.ng/api/item/search?page=1&size=10&subcat_name=cars&title=Peugeot%20Cars%20in%20Nigeria&make=11100&make_t=Peugeot&cityName=&city=Nigeria",
        "https://olist.ng/api/item/search?page=1&size=10&subcat_name=cars&title=Ford%20Cars%20in%20Nigeria&make=11101&make_t=Ford&cityName=&city=Nigeria",
        "https://olist.ng/api/item/search?page=1&size=10&subcat_name=cars&title=Acura%20Cars%20in%20Nigeria&make=11102&make_t=Acura&cityName=&city=Nigeria",
        "https://olist.ng/api/item/search?page=1&size=10&subcat_name=cars&title=Audi%20Cars%20in%20Nigeria&make=11106&make_t=Audi&cityName=&city=Nigeria",
        "https://olist.ng/api/item/search?page=1&size=10&subcat_name=cars&title=BMW%20Cars%20in%20Nigeria&make=11111&make_t=BMW&cityName=&city=Nigeria",
        "https://olist.ng/api/item/search?page=1&size=10&subcat_name=cars&title=Hyundai%20Cars%20in%20Nigeria&make=11141&make_t=Hyundai&cityName=&city=Nigeria",
        "https://olist.ng/api/item/search?page=1&size=10&subcat_name=cars&title=Kia%20Cars%20in%20Nigeria&make=11152&make_t=Kia&cityName=&city=Nigeria",
        "https://olist.ng/api/item/search?page=1&size=10&subcat_name=cars&title=Lexus%20Cars%20in%20Nigeria&make=11157&make_t=Lexus&cityName=&city=Nigeria",
        "https://olist.ng/api/item/search?page=1&size=10&subcat_name=cars&title=Mazda%20Cars%20in%20Nigeria&make=11166&make_t=Mazda&cityName=&city=Nigeria",
        "https://olist.ng/api/item/search?page=1&size=10&subcat_name=cars&title=Volvo%20Cars%20in%20Nigeria&make=11201&make_t=Volvo&cityName=&city=Nigeria",
    ]

    def parse(self, response):
        jsn = json.loads(response.text)
        data_list = jsn["data"]["items"]  # Details page information list
        link_list = []
        for (
            data
        ) in data_list:  # No link to the details page is given, Need to splice links
            item_id = data.get("item_id")
            title = data.get("title")
            detail_url = (
                "https://olist.ng/cars/"
                + "-".join(title.split(" "))
                + "-"
                + str(item_id)
                + ".html"
            )
            link_list.append(detail_url)
        yield from response.follow_all(link_list, self.product_detail)

        last_number = math.ceil(jsn["data"]["total_count"] / 10)  # Round up
        current_page = re.findall("page=(.*?)&", response.url, re.S)[0]
        pagination_links = [
            response.url.replace(f"page={current_page}", f"page={i}")
            for i in range(int(current_page) + 1, int(last_number + 1))
        ]  # all page link
        if int(current_page) + 1 < int(last_number + 1):
            yield from response.follow_all(pagination_links, self.parse)

    def product_detail(self, response):
        output = {}
        ex = "window.__INITIAL_STATE__ = (.*?)</script>"
        jsn = re.findall(ex, response.text, re.S)[0].strip()
        jsn = json.loads(jsn)["detail"]["detailData"].get(
            "info"
        )  # Product details of the current page

        for i in jsn["attrs"]:  # Loop out the required data
            key = i.get("name")
            value = i.get("value")
            if key == "make":
                output["make"] = value
            elif key == "model":
                output["model"] = value
            elif "year" in key:
                output["year"] = int(value)
            elif key == "transmission":
                output["transmission"] = value
            elif key == "mileage":
                output["odometer_value"] = int(value)
                output["odometer_unit"] = re.findall(
                    "Mileage \((.*?)\)", i.get("label"), re.S
                )[0]
            elif key == "type":
                output["fuel"] = value

        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "Olist"
        output["scraped_listing_id"] = jsn["item_id"]
        output["vehicle_url"] = response.url
        output["picture_list"] = json.dumps(
            ["https://static-uc.olist.ng/upload/" + i for i in jsn["photos"]]
        )
        output["city"] = jsn["city_name"]
        output["country"] = "Nigeria"
        output["price_retail"] = float(jsn["price"])
        output["price_wholesale"] = float(jsn["price"])
        output["currency"] = "NGN"

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
