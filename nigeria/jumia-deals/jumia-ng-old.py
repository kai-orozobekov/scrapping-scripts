import scrapy
import os
import json
import datetime

# import apify


class JumiaDeals(scrapy.Spider):
    name = "jumia"
    download_timeout = 120
    start_urls = ["https://deals.jumia.com.ng/cars"]

    def parse(self, response):
        product_links = response.xpath(
            "//a[@class='post-link post-vip']/@href"
        ).getall()
        product_links = ["https://deals.jumia.com.ng" + link for link in product_links]
        yield from response.follow_all(product_links, callback=self.detail)

        next_link = response.xpath("//li[@class='next']/a/@href").get()
        if next_link is not None:
            yield response.follow(
                "https://deals.jumia.com.ng" + next_link, callback=self.parse
            )

    def detail(self, response):
        output = {}
        keys = response.xpath("//div[@class='new-attr-style']/h3/text()").getall()
        values = response.xpath(
            "//div[@class='new-attr-style']/h3/span/text()"
        ).getall()

        # make, model, transmission, fuel, year, odometer_value
        if keys:
            del keys[0]
            output["make"] = response.xpath(
                "//div[@class='new-attr-style']/h3/span/a/text()"
            ).get()
            for i in range(len(keys)):
                if keys[i] == "Model":
                    output["model"] = values[i]

                elif keys[i] == "Transmission":
                    output["transmission"] = values[i]

                elif keys[i] == "Fuel":
                    output["fuel"] = values[i]

                elif keys[i] == "Year":
                    output["year"] = int(values[i])

                elif keys[i] == "Mileage":
                    output["odometer_value"] = int(values[i])

        # ac_installed, tpms_installed, scraped_date, scraped_from, scraped_listing_id, vehicle_url
        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "Jumia Deals"
        output["scraped_listing_id"] = response.url.split("-")[-1].replace("pid", "")
        output["vehicle_url"] = response.url

        # picture_list, city, country, price_retail, price_wholesale, currency
        output["picture_list"] = json.dumps(
            [
                "https://deals.jumia.com.ng" + link
                for link in response.xpath(
                    "//img[@itemprop='image']/@data-src"
                ).getall()
            ]
        )
        output["city"] = response.xpath("//dd[@itemprop='address']/span/text()").get()
        output["country"] = "Nigeria"
        output["price_retail"] = float(
            response.xpath("//span[@itemprop='price']/text()").get().replace(",", "")
        )
        output["price_wholesale"] = output["price_retail"]
        output["currency"] = response.xpath(
            "//span[@itemprop='priceCurrency']/text()"
        ).get()

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
