import datetime
import json
import scrapy
from scrapy.selector import Selector

# import apify


class JamaicarsSpider(scrapy.Spider):
    name = "Jamaicars"
    download_timeout = 120
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
    start_urls = [
        "https://www.jamaicars.com/cars-for-sale?page=1",
    ]

    def parse(self, response):
        # Traverse product links
        product_links = response.xpath('//h2[@class="title"]/a/@href').getall()
        for link in product_links:
            yield response.follow(
                "https://www.jamaicars.com" + link,
                callback=self.detail,
            )

        # pagination
        page_link = response.xpath('//a[contains(text(), ">")]/@href').get()
        if page_link is not None:
            yield response.follow(
                "https://www.jamaicars.com" + page_link,
                callback=self.parse,
            )

    def detail(self, response):
        output = {}

        output["ac_installed"] = 0
        output["tpms_installed"] = 0

        # scraping info
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "JaCars"
        output["vehicle_url"] = response.url
        output["scraped_listing_id"] = response.url.split("for-sale-")[1]

        # location details
        output["country"] = "JM"

        # make, model
        details = response.xpath('//span[@class="breadcrumb-item"]//text()').getall()
        output["make"] = details[2]
        output["model"] = details[3]

        # price details
        price_array = response.xpath(
            '//h1[@class="mgb-item d-flex flex-column"]//span[@class="red-color"]//text()'
        ).getall()
        if len(price_array) > 0:
            price = price_array[1].replace(",", "")
            if price.isnumeric():
                output["price_retail"] = float(price)
                output["currency"] = "JMD"

        # other vehicle details
        car_key_features = response.xpath(
            '//table[@class="table table-borderless"]//tr'
        ).getall()

        for k in range(len(car_key_features)):
            key = Selector(text=car_key_features[k]).xpath("//td/text()").get().lower()
            value_array = (
                Selector(text=car_key_features[k]).xpath("//td/strong/text()").getall()
            )
            value = "".join(value_array)
            if key == "registration year":
                if value != "-":
                    output["registration_year"] = value
            elif key == "no. of doors":
                number_of_doors = value.split(" ")[0]
                if number_of_doors != "-" and number_of_doors.isnumeric():
                    output["doors"] = int(number_of_doors)
            elif key == "exterior color":
                output["exterior_color"] = value
            elif key == "steering":
                output["steering_position"] = value
            elif key == "manufacture year":
                if value.isnumeric():
                    output["year"] = int(value)
            elif key == "no. of seats":
                number_of_seats = value.split(" ")[0]
                if number_of_seats != "-" and number_of_seats.isnumeric():
                    output["seats"] = int(number_of_seats)

        car_specifications = response.xpath(
            '//div[@class="d-flex align-items-center"]/span'
        ).getall()

        for k in range(len(car_specifications)):
            icon_class = Selector(text=car_specifications[k]).xpath("//i/@class").get()
            text_array = Selector(text=car_specifications[k]).xpath("//text()").getall()
            value = "".join(text_array).strip()
            if "fa-map-marker-alt" in icon_class:
                if value != "Japan":
                    output["state_or_province"] = value
                else:
                    output["country"] = "JP"
            elif "fa-road" in icon_class:
                output["odometer_value"] = int(value.split(" ")[0].replace(",", ""))
                output["odometer_unit"] = value.split(" ")[1]
            elif "fa-gas-pump" in icon_class:
                output["fuel"] = value
            elif "icon-automatic" in icon_class:
                output["transmission"] = value
            elif "icon-racing" in icon_class:
                if value != "Other":
                    output["drive_train"] = value
            elif "icon-engine" in icon_class:
                output["engine_displacement_value"] = value.split(" ")[0]
                output["engine_displacement_units"] = value.split(" ")[1]

        # pictures
        imgs_temp = response.xpath(
            '//div[@class="image-gallery-thumbnail-inner"]/img/@src'
        ).getall()
        imgs = []
        for img in imgs_temp:
            imgs.append("https:" + img)
        output["picture_list"] = json.dumps(imgs)

        # vehicle options
        options = response.xpath(
            '//div[@class="car-options mgb-item row"]/div[@class="col-md-4 col-6"]//text()'
        ).getall()
        for option in options:
            if option == "Air conditioning":
                output["ac_installed"] = 1

        # description
        description = response.xpath('//div[@class="more-less-content"]//text()').get()
        if description is not None:
            output["vehicle_disclosure"] = description

        # apify.pushData(output)
