import json
import scrapy
import datetime

# import apify


class Encuentra24(scrapy.Spider):
    name = "encuentra"
    download_timeout = 120
    start_urls = ["https://www.encuentra24.com/dominican-en/cars-auto-trucks-used-car"]

    def parse(self, response):
        product_links = response.xpath(
            "//a[@class='ann-ad-tile__title']/@href"
        ).getall()
        product_links = ["https://www.encuentra24.com" + link for link in product_links]
        yield from response.follow_all(product_links, self.detail)

        next_page = response.xpath(
            "//ul[@class='pagination']/li/a[@rel='next']/@href"
        ).get()
        if next_page is not None:
            yield response.follow("https://www.encuentra24.com" + next_page, self.parse)

    def detail(self, response):
        output = {}

        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "encuentra24.com"
        output["scraped_listing_id"] = response.url.split("?")[0].split("/")[-1]
        output["vehicle_url"] = response.url
        output["country"] = "Dominican Republic"

        # used car, ad_info
        output["picture_list"] = json.dumps(
            response.xpath("//div[@class='photo-slider']/a/@href").getall()
        )
        dealer_details = response.xpath("//span[@class='user-name']/text()").extract()
        if len(dealer_details) > 0:
            output["dealer_name"] = dealer_details[0]

        description = response.xpath("//div[@id='desc-advertiser']/text()").extract()
        if len(description) > 0:
            output["vehicle_disclosure"] = " ".join(description)

        description = response.xpath("//div[@class='row-fluid']/text()").extract()
        if len(description) > 0:
            output["vehicle_disclosure"] = " ".join(description).replace("\n", " ")

        info_names = response.xpath(
            "//div[@class='ad-info']/div/div/div/ul/li/span[1]/text()"
        ).getall()
        info_values = response.xpath(
            "//div[@class='ad-info']/div/div/div/ul/li/span[2]/text()"
        ).getall()
        for i in range(len(info_names)):
            info_names[i] = info_names[i].replace(":", "").lower()
            if info_names[i] == "location":
                output["city"] = info_values[i]

            elif info_names[i] == "make":
                output["make"] = info_values[i]

            elif info_names[i] == "model":
                output["model"] = info_values[i]

            elif info_names[i] == "drivetrain":
                output["drive_train"] = info_values[i]

            elif info_names[i] == "style":
                output["body_type"] = info_values[i]

            elif info_names[i] == "body style":
                doors_number = info_values[i].split("-")[0].strip()
                if doors_number.isnumeric():
                    output["doors"] = int(doors_number)

            elif info_names[i] == "seats":
                seats_number = info_values[i].split(" ")[0]
                if seats_number.isnumeric():
                    output["seats"] = int(seats_number)

            elif info_names[i] == "engine":
                output["engine_displacement_value"] = info_values[i]

            elif info_names[i] == "price":

                output["price_retail"] = float(
                    info_values[i].replace("$", "").replace(",", "").replace("RD", "")
                )
                if "RD" in info_values[i]:
                    output["currency"] = "DOP"
                else:
                    output["currency"] = "USD"

        # ad_details
        detail_names = response.xpath(
            "//div[@class='ad-details']/div/div/div/ul/li/span[2]/text()"
        ).getall()
        detail_values = response.xpath(
            "//div[@class='ad-details']/div/div/div/ul/li/span[3]/text()"
        ).getall()
        for i in range(len(detail_names)):
            if detail_names[i] == "Year:":
                output["year"] = int(detail_values[i])

            elif detail_names[i] == "Km:":
                output["odometer_value"] = int(detail_values[i])
                output["odometer_unit"] = "km"

            elif detail_names[i] == "Transmission:":
                if detail_values[i] and detail_values[i] != "\n":
                    output["transmission"] = detail_values[i]

            elif detail_names[i] == "Fuel:":
                output["fuel"] = detail_values[i]

        additional_details_keys = response.xpath(
            "//ul[@class='product-features']/li/span[@class='info-name']/text()"
        ).getall()
        additional_details_values = response.xpath(
            "//ul[@class='product-features']/li/span[@class='info-value']/text()"
        ).getall()
        for i in range(len(additional_details_keys)):
            if (
                additional_details_keys[i] == "Color:"
                or additional_details_keys[i] == "Colour:"
            ):
                output["exterior_color"] = additional_details_values[i]

        additional_features = response.xpath(
            "//div[contains(@class, 'section-container') and contains(@class, 'paragraph-container')]/ul[@class='product-features']/li/text()"
        ).getall()
        if len(additional_features) > 0:
            for feature in additional_features:
                if feature.strip() == "A/C":
                    output["ac_installed"] = 1

        # new car info
        if "make" not in output.keys():
            output["make"] = response.xpath(
                "//ul[@class='d3-breadcrumb__list']/li[4]/a/span/text()"
            ).get()
            attribute_names = response.xpath(
                "//dl[@class='d3-property-insight__attribute-details']/dt/text()"
            ).getall()
            attribute_values = response.xpath(
                "//dl[@class='d3-property-insight__attribute-details']/dd/text()"
            ).getall()
            for i in range(len(attribute_names)):
                if attribute_names[i] == "Model":
                    output["model"] = attribute_values[i]

                elif attribute_names[i] == "Precio":
                    output["price_retail"] = float(
                        attribute_values[i]
                        .replace("$", "")
                        .replace(",", "")
                        .replace(".", "")
                        .replace("RD", "")
                    )
                    output["currency"] = "DOP"

                elif attribute_names[i] == "Year":
                    output["year"] = int(attribute_values[i])

                elif attribute_names[i] == "Fuel":
                    output["fuel"] = attribute_values[i]

                elif attribute_names[i] == "Kilometers":
                    output["odometer_value"] = int(attribute_values[i].replace("'", ""))
                    output["odometer_unit"] = "km"

            property_names = response.xpath(
                "//div[@class='d3-property-details__content']/div/text()"
            ).getall()
            property_values = response.xpath(
                "//div[@class='d3-property-details__content']/div/p/text()"
            ).getall()

            for i in range(len(property_names)):
                if property_names[i] == "Location":
                    output["city"] = property_values[i]

                elif property_names[i] == "Engine":
                    output["engine_displacement_value"] = property_values[i]

                elif property_names[i] == "Transmission":
                    output["transmission"] = property_values[i]

                elif property_names[i] == "Style":
                    output["body_type"] = property_values[i]

                elif property_names[i] == "Drivetrain":
                    output["drive_train"] = property_values[i]

                elif property_names[i] == "Category":
                    if "new" in property_values[i].lower():
                        output["is_used"] = 0

                elif property_names[i] == "Seats":
                    output["seats"] = int(property_values[i].split(" ")[0])

            output["picture_list"] = json.dumps(
                response.xpath(
                    "//div[@class='d3-photos-grid__items']/div/div/img/@src"
                ).getall()
            )
            output["city"] = (
                response.xpath(
                    "//div[@class='d3-property-headline__text']/div[2]/text()[2]"
                )
                .get()
                .replace("\n", "")
            )
            description = response.xpath(
                "//div[@class='d3-property-about__text']/text()"
            ).extract()
            output["vehicle_disclosure"] = " ".join(description)

        # apify.pushData(output)
