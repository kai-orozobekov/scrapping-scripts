import datetime
import json
import scrapy
from scrapy.selector import Selector

# import apify


class DrivecomSpider(scrapy.Spider):
    name = "Drivecom"
    download_timeout = 120
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
    start_urls = [
        "https://www.drive.com.au/cars-for-sale/all/all/page/1/",
    ]

    def parse(self, response):
        total_count = response.xpath(
            "//p[@class='leftFilters_drive-cfs__left-filters__count__KILoW']//text()"
        ).get()
        total_count = int(total_count.replace(",", "").replace("Cars", "").strip())
        total_pages = round(total_count / 20)
        links_to_pages = []

        for k in range(total_pages):
            links_to_pages.append(
                "https://www.drive.com.au/cars-for-sale/all/all/page/"
                + str(k + 1)
                + "/"
            )

        yield from response.follow_all(
            links_to_pages,
            callback=self.traverse_product_links,
        )

    def traverse_product_links(self, response):
        product_links = response.xpath(
            '//a[@class="listingDetailsCard_drive-cfs__listing-card__enquiry-modal-btn-wrapper__EIAhs"]/@href'
        ).getall()
        yield from response.follow_all(
            product_links,
            callback=self.detail,
        )

    def detail(self, response):
        output = {}

        output["ac_installed"] = 0
        output["tpms_installed"] = 0

        # scraping info
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "Drivecom"
        output["vehicle_url"] = response.url
        output["scraped_listing_id"] = response.url.split("/")[-2]
        output["country"] = "AU"

        description = response.xpath(
            "//div[@class='sellerComments_drive-cfs__seller-comment__wrapper__sgHAF']//text()"
        ).get()
        if description is not None:
            output["vehicle_disclosure"] = description

        car_key_features = response.xpath(
            "//div[@class='keyFeatures_drive-cfs__listing__key-features__container__e8jgh']//div[@class='features_drive-cfs__listing__feature__wrapper__il_V3']"
        ).getall()
        for k in range(len(car_key_features)):
            key = (
                Selector(text=car_key_features[k])
                .xpath(
                    "//div[@class='features_drive-cfs__listing__feature__name__JjIZ_']/text()"
                )
                .get()
            )
            value = (
                Selector(text=car_key_features[k])
                .xpath(
                    "//span[@class='features_drive-cfs__listing__feature__value-label__3De_8']/text()"
                )
                .get()
            )
            if value != "-" and value is not None:
                key = key.lower()
                value = value.lower()
                if key == "make":
                    output["make"] = value
                elif key == "model":
                    output["model"] = value
                elif key == "variant":
                    output["trim"] = value
                elif key == "color":
                    output["exterior_color"] = value
                elif key == "odometer":
                    if value != "na":
                        output["odometer_value"] = int(
                            value.replace("kms", "").replace(",", "")
                        )
                        output["odometer_unit"] = "km"
                elif key == "year":
                    output["year"] = int(value)
                elif key == "vin":
                    output["vin"] = value

        car_overview_details = response.xpath(
            "//div[@class='specTable_drive-cfs__spec-table__wrapper__VfGdU']//div[@class='tab accordion_drive-accordion__VCu0k md:pb-6']"
        ).getall()
        for k in range(len(car_overview_details)):
            containers = (
                Selector(text=car_overview_details[k])
                .xpath(
                    "//div[@class='specTableSection_drive-cfs__spec-table__section__wrapper__ToqBT']"
                )
                .getall()
            )

            for i in range(len(containers)):
                rows = (
                    Selector(text=containers[i])
                    .xpath(
                        "//div[@class='specTableSection_drive-cfs__spec-table__section__item-wrapper__WFI7B']"
                    )
                    .getall()
                )
                for r in range(len(rows)):
                    key = (
                        Selector(text=rows[r])
                        .xpath(
                            "//div[@class='features_drive-cfs__listing__feature__name__JjIZ_']/text()"
                        )
                        .get()
                    )

                    value = (
                        Selector(text=rows[r])
                        .xpath(
                            "//span[@class='features_drive-cfs__listing__feature__value-label__3De_8']/text()"
                        )
                        .get()
                    )

                    if value is not None:
                        key = key.lower()
                        value = value.lower().strip()
                        if value != "-":
                            if key == "body type":
                                output["body_type"] = value
                            elif key == "build country":
                                output["country_of_manufacture"] = value
                            elif key == "doors":
                                output["doors"] = int(value)
                            elif key == "seats":
                                output["seats"] = int(value)
                            elif key == "cylinders":
                                number_of_cylinders = [
                                    int(s) for s in value if s.isdigit()
                                ]
                                output["engine_cylinders"] = number_of_cylinders[0]
                            elif key == "engine size":
                                unit = "".join(x for x in value if x.isalpha())
                                output["engine_displacement_units"] = unit
                                output["engine_displacement_value"] = value.replace(
                                    unit, ""
                                )
                            elif key == "drive type":
                                output["drive_train"] = value
                            elif key == "transmission type":
                                output["transmission"] = value
                            elif key == "fuel type":
                                output["fuel"] = value

        location_array = response.xpath(
            "//div[@class='listingInfo_drive-cfs__listing__dealer-info__location__FX_v_']/text()"
        ).getall()
        if len(location_array) > 0:
            location = "".join(location_array[: len(location_array) // 2])
            city = location.split(",")[0].strip()
            sop = location.split(",")[1].strip()
            if len(city) > 0:
                output["city"] = city
            if len(sop) > 0:
                output["state_or_province"] = sop

        price = response.xpath(
            "//p[@class='listingInfo_drive-cfs__listing-info__price__k52va']//text()"
        ).getall()

        if price[1].replace(",", "").isnumeric():
            output["price_retail"] = float(price[1].replace(",", ""))
            output["currency"] = "AUD"

        imgs_initial = response.xpath(
            "//figure[@class='heroAndInfo_drive-cfs__hero-carousel__figure__wcKts']/img/@src"
        ).getall()
        filtered_imgs = []
        for img in imgs_initial:
            if "cfs-default-image-desktop" not in img:
                filtered_imgs.append(img)

        if len(filtered_imgs) > 0:
            output["picture_list"] = json.dumps(filtered_imgs)

        # print(output)
        print("\n")
        # apify.pushData(output)
