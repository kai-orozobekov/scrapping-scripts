import json
import datetime

import scrapy
from scrapy import Request, Selector

# import apify


class AutocosmosSpider(scrapy.Spider):
    name = "Autocosmos"
    # allowed_domains = ['www.autocosmos.cl']
    start_urls = ["https://www.autocosmos.cl/auto/usado/"]

    def parse(self, response):
        sel = Selector(response)
        href_list = sel.xpath('//article[@class="card listing-card "]/a/@href').getall()
        for href in href_list:
            url = "http://www.autocosmos.cl" + href
            yield Request(url, meta={"vehicle_url": url}, callback=self.get_data)

        # next page
        next_href = sel.xpath('//a[has-class("m-next")]/@href').get()
        if next_href:
            yield Request("http://www.autocosmos.cl" + next_href)

    def get_data(self, response):
        sel = Selector(response)

        output = {}

        # defualt
        output["vehicle_url"] = str(response.meta["vehicle_url"])
        output["scraped_listing_id"] = response.meta["vehicle_url"].split("/")[-1]
        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        output["country"] = "Chile"
        output["scraped_from"] = "Autocosmos"
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())

        # get title
        output["make"] = (
            sel.xpath('//h1[@class="car-specifics__name"]/text()').get().strip()
        )
        output["model"] = (
            sel.xpath('//span[@class="car-specifics__model"]/text()').get().strip()
        )

        output["city"] = sel.xpath(
            '//section[@class="car-specifics"]//span[@itemprop="addressLocality"]/text()'
        ).get()

        # get picture
        picture = (
            sel.css("div.slide-container")
            .xpath(
                './/source[contains(@media,"(min-width:800px)")]/@data-gallery-slider-img-srcset'
            )
            .getall()
        )
        if picture:
            picture = json.dumps(picture)
            output["picture_list"] = picture

        # get price
        price = sel.xpath('//strong[contains(@itemprop,"price")]/@content').get()
        if price:
            try:
                price = float(price)
                output["price_retail"] = price
                output["currency"] = "CLP"
            except TypeError:
                pass

        modelDate = (
            sel.css("div.car-specifics__extra-info")
            .xpath('.//span[contains(@itemprop,"modelDate")]/text()')
            .get()
        )
        if modelDate:
            try:
                output["year"] = int(modelDate)
            except TypeError:
                pass

        mileageFromOdometer = (
            sel.css("div.car-specifics__extra-info")
            .xpath('.//span[contains(@itemprop,"mileageFromOdometer")]/text()')
            .get()
        )
        if mileageFromOdometer:
            try:
                output["odometer_value"] = int(mileageFromOdometer.split(" ")[0])
                output["odometer_unit"] = mileageFromOdometer.split(" ")[1]
            except (TypeError, IndexError):
                pass

        detail_list = sel.xpath(
            '//div[@class="section-container"]/section[@class="section"][1]//div[@class="grid-container__content m-full"]/div//tr'
        )
        for detail in detail_list:
            content = detail.xpath("./td/text()").getall()
            key = content[0]
            try:
                value = content[1]
            except IndexError:
                continue

            if key == "Combustible":
                output["fuel"] = value

            elif key == "Cilindrada":
                output["engine_displacement_value"] = value.split(" ")[0]
                try:
                    output["engine_displacement_units"] = value.split(" ")[1]
                except IndexError:
                    pass

            elif key == "Cilindros":
                if value != "N/A"
                output["engine_cylinders"] = value

        # apify.pushData(output)
        yield output
