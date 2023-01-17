import datetime
import json
import scrapy

# import apify


class YaDriveImportsSpider(scrapy.Spider):
    name = "YaDriveImports"
    download_timeout = 120
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
    start_urls = [
        "http://yardriveimports.com/search?make_id=&model_id=&fuel=&drivetrain=&price_from=&price_to=&body_type=&steering=&transmission=&mileage_from=&mileage_to=&engine_capacity_from=&engine_capacity_to=&year_from=&year_to=",
    ]

    def parse(self, response):
        makes_ids = response.xpath(
            '//select[@id="make_id"]/option[not(@id)]/@value'
        ).getall()
        makes_values = response.xpath('//select[@id="make_id"]/option/text()').getall()

        for k in range(len(makes_ids)):
            yield response.follow(
                f"http://yardriveimports.com/search?make_id={makes_ids[k]}&model_id=&fuel=&drivetrain=&price_from=&price_to=&body_type=&steering=&transmission=&mileage_from=&mileage_to=&engine_capacity_from=&engine_capacity_to=&year_from=&year_to=",
                callback=self.traverse_product_links,
                meta={"make": makes_values[k]},
            )

    def traverse_product_links(self, response):
        # Traverse product links
        product_links = response.xpath(
            '//a[@class="search__item-inquiry"]/@href'
        ).getall()
        for link in product_links:
            yield response.follow(
                "http://yardriveimports.com" + link,
                callback=self.detail,
                meta={"make": response.meta["make"]},
            )

        # pagination
        page_link = response.xpath('//a[contains(text(), "NEXT")]/@href').get()
        if page_link is not None:
            yield response.follow(
                "http://yardriveimports.com" + page_link,
                callback=self.traverse_product_links,
                meta={"make": response.meta["make"]},
            )

    def detail(self, response):
        output = {}

        output["ac_installed"] = 0
        output["tpms_installed"] = 0

        # scraping info
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "YaDriveImports"
        output["vehicle_url"] = response.url
        output["scraped_listing_id"] = response.url.split("/")[-1].split("#")[0]

        # location details
        output["country"] = "JM"

        # make, model
        make = response.meta["make"]
        model = (
            response.xpath('//h1[@class="detail__title"]//text()')
            .get()
            .replace(make, "")
            .strip()
        )
        output["make"] = make.lower()
        output["model"] = model

        # pricing details
        price = response.xpath('//strong[@class="detail__now-price"]//text()').get()
        output["price_retail"] = float(price.replace("$", "").replace(",", ""))
        output["currency"] = "USD"

        # pictures
        imgs = json.loads(
            response.xpath(
                '//section[@class="detail_slider-container"]//div[@data-component="photo-slider"]/@data-props'
            ).get()
        )
        output["picture_list"] = json.dumps(imgs["images"])

        # vehicle specs
        specs_keys = response.xpath('//div[@class="detail__spec-key"]//text()').getall()
        specs_values = response.xpath(
            '//div[@class="detail__spec-value"]//text()'
        ).getall()
        for k in range(len(specs_keys)):
            key = specs_keys[k].strip().lower()
            value = specs_values[k].strip().lower()
            if value != "-":
                if key == "chassis #":
                    output["chassis_number"] = value
                elif key == "mileage":
                    if "km" in value:
                        output["odometer_value"] = int(
                            value.replace(",", "").replace("km", "")
                        )
                        output["odometer_unit"] = "km"
                elif key == "engine size":
                    if "cc" in value:
                        output["engine_displacement_value"] = value.replace(
                            ",", ""
                        ).replace("cc", "")
                        output["engine_displacement_units"] = "cc"
                elif key == "ext. color":
                    output["exterior_color"] = value
                elif key == "wheel drive":
                    output["drive_train"] = value
                elif key == "registration year/month":
                    output["registration_year"] = value
                elif key == "manufacture year/month":
                    output["year"] = int(value.split("/")[0])
                elif key == "doors":
                    if value.isnumeric():
                        output["doors"] = int(value)
                elif key == "seats":
                    if value.isnumeric():
                        output["seats"] = int(value)
                elif key == "fuel":
                    output["fuel"] = value
                elif key == "steering":
                    output["steering_position"] = value
                elif key == "transmission":
                    output["transmission"] = value

        # vehicle features
        features = response.xpath('//div[@class="detail__feature"]//text()').getall()
        for feature in features:
            feature = feature.lower()
            if feature == "leather seat":
                output["upholstery"] = "leather"
            elif feature == "a/c":
                output["ac_installed"] = 1

        # apify.pushData(output)
