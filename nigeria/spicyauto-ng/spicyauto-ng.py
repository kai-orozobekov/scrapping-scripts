import scrapy
import json
import datetime

# import apify


class SpicyAuto(scrapy.Spider):
    name = "spicy"
    download_timeout = 120
    start_urls = ["https://www.spicyauto.com/cars?page=1"]

    def parse(self, response):
        # Traverse product links
        product_links = response.xpath(
            "//div[@class='row whitBg2']/div/a/@href"
        ).getall()
        product_links = [link for link in product_links if link != "javascript:;"]
        yield from response.follow_all(product_links, self.detail)

        # pagination
        next_page = response.xpath(
            "//ul[@class='pagination']/li/a[@rel='next']/@href"
        ).get()
        if next_page is not None:
            yield response.follow(next_page, self.parse)

    def detail(self, response):
        output = {}

        # make, model
        output["make"] = response.xpath(
            "//ul[@class='list-inline']/li[4]/a/text()"
        ).get()
        output["model"] = response.xpath(
            "//ul[@class='list-inline']/li[5]/a/text()"
        ).get()

        row_keys = response.xpath(
            "//div[@class='row marginSid'][1]/div/p/strong/text()"
        ).getall()
        row_values = response.xpath(
            "//div[@class='row marginSid'][1]/div/p/text()[2]"
        ).getall()

        row_values = [
            value.replace("\n", "").replace("\xa0", "").strip()
            for value in row_values
            if value not in ("\n", "")
        ]

        for i in range(len(row_keys)):
            if row_values[i].lower() != "none" and row_values[i].lower() != "other":
                if row_keys[i] == "Fuel Type":
                    output["fuel"] = row_values[i]

                elif row_keys[i] == "Transmission":
                    output["transmission"] = row_values[i]

                elif row_keys[i] == "Year":
                    output["year"] = int(row_values[i])

                elif row_keys[i] == "Trim":
                    output["trim"] = row_values[i]

                elif row_keys[i] == "Body Type":
                    output["body_type"] = row_values[i]

                elif row_keys[i] == "Drive Type":
                    output["drive_train"] = row_values[i]

                elif row_keys[i] == "Drive Setup":
                    output["steering_position"] = row_values[i].split(" ")[0]

                elif row_keys[i] == "Interior Type":
                    output["upholstery"] = row_values[i]

                elif row_keys[i] == "Colour":
                    output["exterior_color"] = row_values[i]

                elif row_keys[i] == "Door Count":
                    output["doors"] = int(row_values[i])

                elif row_keys[i] == "Mileage(km)":
                    output["odometer_value"] = int(row_values[i].replace(",", ""))
                    output["odometer_unit"] = "km"

        # ac_installed, tpms_installed, scraped_date, scraped_from, scraped_listing_id, vehicle_url
        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "SpicyAuto"
        output["scraped_listing_id"] = response.url.split("-")[-1]
        output["vehicle_url"] = response.url

        output["vehicle_disclosure"] = response.xpath(
            "//div[@class='row marginSid'][2]/div[contains(@class, 'col-sm-12') and contains(@class, 'col-xs-12')]/p/text()"
        ).get()

        features = response.xpath("//p[@class='shadOpt']/text()").getall()
        for feature in features:
            if feature.strip().lower() == "air conditioning":
                output["ac_installed"] = 1

        # picture_list
        pictures = response.xpath(
            "//div[@class='fotorama fullscreen']/img/@src"
        ).getall()

        output["picture_list"] = json.dumps(
            [src.replace("../../", "https://www.spicyauto.com/") for src in pictures]
        )

        # city, country
        output["city"] = (
            response.xpath("//div[@class='col-sm-7']/p/text()")
            .get()
            .split("|")[0]
            .strip()
        )
        output["country"] = "Nigeria"

        # price_retail, currency
        output["price_retail"] = float(
            response.xpath("//div[@class='col-sm-3']/h4/text()")
            .get()
            .replace("₦", "")
            .replace(",", "")
            .strip()
        )
        output["currency"] = "NGN"

        # apify.pushData(output)
