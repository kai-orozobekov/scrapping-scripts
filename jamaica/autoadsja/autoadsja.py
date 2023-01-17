import datetime
import json
import scrapy
from scrapy.selector import Selector

# import apify


class AutoadsjaSpider(scrapy.Spider):
    name = "AutoAdsJA"
    download_timeout = 120
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
    start_urls = [
        "https://www.autoadsja.com/search.asp?SearchSB=5&page=1",
    ]

    def parse(self, response):
        # Traverse product links
        product_links = response.xpath('//div[@class="thumbnail"]//a/@href').getall()
        yield from response.follow_all(
            product_links,
            callback=self.detail,
        )

        # pagination
        page_link = response.xpath('//a[@class="btn btn-lg btn-success"]/@href').get()
        if page_link is not None:
            yield response.follow(
                "https://www.autoadsja.com/search.asp" + page_link,
                callback=self.parse,
            )

    def detail(self, response):
        output = {}

        output["ac_installed"] = 0
        output["tpms_installed"] = 0

        # scraping info
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "AutoAdsJA"
        output["vehicle_url"] = response.url
        output["scraped_listing_id"] = response.url.split("/")[-1]
        output["country"] = "JM"

        imgs = response.xpath('//div[@class="gallery__main"]//img/@src').getall()
        output["picture_list"] = json.dumps(imgs)

        price_retail = response.xpath(
            '//div[@class="col-md-12 col-sm-12 col-xs-12 price-tag"]/h2/span/text()'
        ).get()
        if price_retail is not None:
            output["price_retail"] = float(
                price_retail.replace("$", "").replace(",", "")
            )
            output["currency"] = "JMD"

        details = response.xpath('//div[@class="per-detail"]//ul/li/text()').getall()
        for detail in details:
            key = detail.split(":")[0].lower()
            value = detail.split(":")[1].lower().strip()
            if "location" in key:
                output["state_or_province"] = value
            elif "body type" in key:
                output["body_type"] = value
            elif "driver side" in key:
                output["steering_position"] = value
            elif "drive type" in key:
                output["drive_train"] = value
            elif "transmission" in key:
                output["transmission"] = value
            elif "fuel type" in key:
                output["fuel"] = value
            elif "cc rating" in key:
                output["engine_displacement_value"] = value
                output["engine_displacement_units"] = "cc"
            elif "mileage" in key:
                mileage = value.replace("km", "").replace(",", "")
                if mileage.isnumeric():
                    output["odometer_value"] = int(mileage)
                    output["odometer_unit"] = "km"

        description = response.xpath('//p[@class="vehicle-description"]//text()').get()
        if description is not None:
            output["vehicle_disclosure"] = description.strip()

        vehicle_m_details = response.xpath(
            '//ul[@class="breadcrumb "]/li//text()'
        ).getall()
        output["make"] = vehicle_m_details[3]
        output["model"] = vehicle_m_details[4]
        title = response.xpath(
            '//div[@class="col-md-12 col-sm-12 col-xs-12 price-tag"]/h1//text()'
        ).get()
        year = title.split(" ")[0]
        if year.isnumeric():
            output["year"] = int(year)

        status = response.xpath(
            '//div[@class="material-msg text-center"]/p/text()'
        ).get()
        if status is not None:
            if status == "This Vehicle is no longer available":
                output["status"] = "sold"

        # apify.pushData(output)
