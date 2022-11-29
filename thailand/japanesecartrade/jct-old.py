import gc
import os
import json
import re
import scrapy
import datetime
from scrapy.http.response import Response

import apify


class JpcartradeSpider(scrapy.Spider):
    name = "jpcartrade"
    download_timeout = 120

    def __init__(self):
        self.form_data = {
            "per_page": "",
            "page": "0",
            "sort": "",
            "seq": "",
            "make_id": "",
            "maker_id": "",
            "mfg_from": "",
            "month_from": "",
            "mfg_to": "",
            "month_to": "",
            "fuel_id": "",
            "seat_capacity": "",
            "transmission_id": "",
            "type_id": "",
            "subtype_id": "",
            "drive": "",
            "mileage_from": "",
            "mileage_to": "",
            "price_from": "",
            "price_to": "",
            "cc_from": "",
            "cc_to": "",
            "wheel_drive": "",
            "color_id": "",
            "stock_country": "thailand",
            "search_keyword": "",
            "SA": "make",
            "isSearched": "1",
            "desksearch": "desksearch",
        }

    def start_requests(self):
        url = "https://www.japanesecartrade.com/stock_list.php?make_id=&maker_id=&mfg_from=&month_from=&mfg_to=&month_to=&fuel_id=&seat_capacity=&transmission_id=&type_id=&subtype_id=&drive=&mileage_from=&mileage_to=&price_from=&price_to=&cc_from=&cc_to=&wheel_drive=&color_id=&stock_country=thailand&search_keyword=&SA=make&isSearched=1&sort=&desksearch=desksearch&seq="
        yield scrapy.FormRequest(
            url=url,
            formdata=self.form_data,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_context": datetime.datetime.isoformat(
                    datetime.datetime.today()
                ),
            },
            callback=self.parse,
            errback=self.errback_close_page,
        )

    async def parse(self, response: Response):
        page = response.meta["playwright_page"]
        await page.context.close()  # close the context
        await page.close()
        del page
        gc.collect()

        car_list = response.xpath(
            '//div[@class="ListHeader "]/div//h2/a/@href'
        ).getall()
        for link in car_list:
            yield scrapy.Request(
                url=link,
                callback=self.detail,
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,
                    playwright_context=datetime.datetime.isoformat(
                        datetime.datetime.today()
                    ),
                ),
                errback=self.errback_close_page,
            )

        next_button = response.xpath('//a[contains(@aria-label, "Next")]/@href').get()
        if next_button:
            next_button = re.findall(
                "javascript:redirectPage\\('(.*?)'\\)", next_button, re.S
            )
            self.form_data["page"] = str(next_button[0])
            yield scrapy.FormRequest(
                url=response.url,
                formdata=self.form_data,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_context": datetime.datetime.isoformat(
                        datetime.datetime.today()
                    ),
                },
                callback=self.parse,
                errback=self.errback_close_page,
            )

    async def detail(self, response):
        page = response.meta["playwright_page"]
        await page.context.close()  # close the context
        await page.close()
        del page
        gc.collect()

        output = {}

        form_data = response.xpath(
            "//div[@class='col-lg-4 col-md-4 col-sm-3 col-xs-6']"
        )
        for data in form_data:
            key = data.xpath("./div[1]/text()").get()
            value = data.xpath("./div[2]/text()").get()
            if "Make" in key:
                output["make"] = value
            elif key.lower() == "model":
                output["model"] = value

        form_data2 = response.xpath("//div[contains(@class, 'dtl_main_spec')]/div")
        for data2 in form_data2:
            key = data2.xpath("./span/@aria-label").get()
            value = data2.xpath("./text()").get()
            if key:
                if "Year" in key:
                    year = value.split("/")[0]
                    if year.isdigit():
                        output["year"] = int(year)
                elif "Transmission" in key:
                    output["transmission"] = value
                elif "Engine" in key:
                    output["engine_displacement_value"] = value.split(" ")[0]
                    output["engine_displacement_units"] = value.split(" ")[1]
                elif "Fuel" in key:
                    output["fuel"] = value
                elif "Mileage" in key:
                    output["odometer_value"] = int(value.split(" ")[0].replace(",", ""))
                    output["odometer_unit"] = value.split(" ")[1]
                elif "Stock" in str(key):
                    if value == "Thailand":
                        output["country"] = "TH"

        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "JapaneseCarTrade"
        output["scraped_listing_id"] = re.findall(
            "japanesecartrade.com/(.*?)-", response.url, re.S
        )[0]
        output["vehicle_url"] = response.url

        price = response.xpath("//div[@class='detail_price']//strong/text()").get()
        price = "".join([i for i in list(price) if i.isdigit()])
        if price:
            output["price_retail"] = float(price)
            output["currency"] = "USD"

        picture_list = response.xpath("//img[@id='main_photo']/@src").get()
        if picture_list:
            output["picture_list"] = json.dumps(picture_list)

        # yield output
        apify.pushData(output)

    async def errback_close_page(self, failure):
        print("page close", failure.request.url)
        page = failure.request.meta["playwright_page"]
        await page.context.close()  # close the context
        await page.close()
        del page
        gc.collect()
