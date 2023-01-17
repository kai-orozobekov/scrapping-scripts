import datetime
import json
import scrapy

# import apify


class JacarsSpider(scrapy.Spider):
    name = "JaCars"
    download_timeout = 120
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
    start_urls = [
        "https://www.jacars.net/cars/?type_view=card",
    ]

    def parse(self, response):
        total_pages = response.xpath(
            "//a[@class='page-number js-page-filter ']//text()"
        ).getall()
        last_page = int(total_pages[-1])
        links_to_pages = []

        for k in range(1, last_page + 1):
            links_to_pages.append(
                "https://www.jacars.net/cars/?type_view=card&page=" + str(k)
            )

        yield from response.follow_all(
            links_to_pages,
            callback=self.traverse_product_links,
        )

    def traverse_product_links(self, response):
        # Traverse product links
        product_links = response.xpath(
            '//a[@class="mask"]/@href|//a[@class="mask "]/@href'
        ).getall()
        for link in product_links:
            yield response.follow(
                "https://www.jacars.net" + link,
                callback=self.detail,
            )

    def detail(self, response):
        output = {}

        output["ac_installed"] = 0
        output["tpms_installed"] = 0

        # scraping info
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "JaCars"
        output["vehicle_url"] = response.url
        output["scraped_listing_id"] = response.xpath(
            '//span[@itemprop="sku"]//text()'
        ).get()

        # location details
        output["country"] = "JM"
        output["state_or_province"] = response.xpath(
            '//span[@itemprop="address"]//text()'
        ).get()

        # pictures
        imgs = response.xpath(
            '//img[@class="announcement__images-item js-image-show-full"]/@src'
        ).getall()
        output["picture_list"] = json.dumps(imgs)

        # make, mode
        vehicle_basic_details = response.xpath(
            '//ul[@class="breadcrumbs"]//span[@itemprop="name"]//text()'
        ).getall()
        if len(vehicle_basic_details) > 3:
            output["make"] = vehicle_basic_details[2]
            output["model"] = vehicle_basic_details[3]

        # price details
        price_array = response.xpath(
            '//div[contains(@class, "announcement-price__cost")]/text()'
        ).getall()
        price_discount = response.xpath(
            '//span[@class="announcement-price__discount-start"]/text()'
        ).get()

        price = None
        for item in price_array:
            item = item.strip().replace("\n", "")
            if len(item) > 0:
                price = item.replace(",", "")
        if price is not None and price.isnumeric():
            output["price_retail"] = float(price)
            output["currency"] = "JMD"

        if price_discount is not None and "price_retail" in output:
            output["promotional_price"] = output["price_retail"]
            output["price_retail"] = float(price_discount.replace(",", ""))

        # description
        description_array = response.xpath(
            '//div[@class="js-description"]/p/text()'
        ).getall()
        description = ""
        for row in description_array:
            row = row.replace("\n", "")
            if len(row) > 0:
                description = description + row + " "

        if description != "":
            output["vehicle_disclosure"] = description

        # vehicle details
        keys = response.xpath('//span[@class="key-chars"]/text()').getall()
        values = response.xpath(
            '//a[@class="value-chars"]/text()|//span[@class="value-chars"]/text()'
        ).getall()

        for i in range(len(keys)):
            key = keys[i].lower().replace(":", "")
            value = values[i].strip()
            if key == "year":
                output["year"] = int(value)
            elif key == "seats":
                output["seats"] = int(value)
            elif key == "colour":
                output["exterior_color"] = value
            elif key == "gearbox":
                output["transmission"] = value
            elif key == "body type":
                output["body_type"] = value
            elif key == "fuel type":
                output["fuel"] = value
            elif key == "drivetrain":
                output["drive_train"] = value
            elif key == "air conditioning":
                if value == "Yes":
                    output["ac_installed"] = 1
            elif key == "engine size":
                if "L" in value:
                    output["engine_displacement_value"] = value.replace("L", "")
                    output["engine_displacement_units"] = "L"
            elif key == "mileage":
                output["odometer_value"] = int(value.split(" ")[0])
                output["odometer_unit"] = value.split(" ")[1]
            elif key == "right hand drive":
                output["steering_position"] = value

        # apify.pushData(output)
