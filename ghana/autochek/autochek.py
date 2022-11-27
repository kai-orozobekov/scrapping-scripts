import scrapy
import datetime
import json
from scrapy.downloadermiddlewares.retry import get_retry_request

# import apify


class Autochek(scrapy.Spider):
    name = "autochek"
    download_timeout = 120
    start_urls = [
        "https://autochek.africa/en/gh/cars-for-sale?country=ng&page_number=1"
    ]

    def parse(self, response):
        jsn = response.xpath("//script[@id='__NEXT_DATA__']").get()
        jsn = (
            str(jsn)
            .replace('<script id="__NEXT_DATA__"', "")
            .replace('type="application/json">', "")
            .replace("</script>", "")
            .strip()
        )
        jsn = json.loads(jsn)

        # traverse vehicle links
        cars = jsn["props"]["pageProps"].get("cars", "")
        if not cars or cars == "":
            new_request_or_none = get_retry_request(
                response.request, spider=self, reason="empty", max_retry_times=10
            )
            yield new_request_or_none
        else:
            product_links = [str(j["websiteUrl"]) for j in cars]
            yield from response.follow_all(
                product_links, self.product_detail, dont_filter=True
            )

            last_number = (
                jsn["props"]["pageProps"]["pagination"]["total"]
                // jsn["props"]["pageProps"]["pagination"]["pageSize"]
            )
            current_page = jsn["props"]["pageProps"]["pagination"]["currentPage"]
            if last_number and current_page:
                if int(current_page) + 1 < int(last_number) + 2:
                    url = response.url.replace(
                        f"page_number={int(current_page)}",
                        f"page_number={int(current_page)+1}",
                    )
                    yield response.follow(url, self.parse)

    def product_detail(self, response):
        output = {}
        jsn = response.xpath("//script[@id='__NEXT_DATA__']").get()
        jsn = (
            str(jsn)
            .replace('<script id="__NEXT_DATA__"', "")
            .replace('type="application/json">', "")
            .replace("</script>", "")
            .strip()
        )
        jsn = dict(json.loads(jsn))
        page_props = jsn["props"]["pageProps"]
        car = page_props.get("car", "")

        if not car or car == "":
            new_request_or_none = get_retry_request(
                response.request, spider=self, reason="empty", max_retry_times=10
            )
            yield new_request_or_none
        else:
            # pictures list
            car_media = page_props["carMediaList"]
            pictures = [item["url"] for item in car_media]
            pictures.append(car["imageUrl"])
            output["picture_list"] = json.dumps(pictures)

            # pricing
            output["price_retail"] = float(car.get("marketplacePrice"))
            output["currency"] = page_props.get("country").get("currency")

            # scraping info
            output["vehicle_url"] = response.url
            output["scraped_date"] = datetime.datetime.isoformat(
                datetime.datetime.today()
            )
            output["scraped_from"] = "AutoChek"
            output["scraped_listing_id"] = str(car.get("id"))

            # location
            output["city"] = car.get("city")
            output["state_or_province"] = car.get("state")
            if page_props.get("country").get("country").lower() == "ghana":
                output["country"] = "GH"

            # odometer
            output["odometer_value"] = int(car.get("mileage"))
            output["odometer_unit"] = car.get("mileageUnit")

            output["ac_installed"] = 0
            output["tpms_installed"] = 0
            inspection_report = page_props.get("inspectionReport")
            if inspection_report is not None:
                output["inspection_description"] = inspection_report.get("pdfReport")
                output["inspection_date"] = inspection_report.get("updatedAt")
                output["inspection_value"] = round(inspection_report.get("score"))

            # basic info - vin, make, model, year
            output["vin"] = car.get("vin")
            output["make"] = car.get("model").get("make").get("name")
            output["model"] = car.get("model").get("name")
            output["year"] = int(car.get("year"))

            output["transmission"] = car.get("transmission")
            output["fuel"] = car.get("fuelType")
            output["body_type"] = car.get("bodyType").get("name")
            output["engine_block_type"] = car.get("engineType")

            # colors
            output["exterior_color"] = car.get("exteriorColor")
            output["interior_color"] = car.get("interiorColor")

            # vehicle features
            features_list = page_props["carFeatureList"]
            for feature in features_list:
                feature_name = feature.get("feature").get("name")
                if feature_name.lower() == "air conditioning":
                    output["ac_installed"] = 1
                if feature_name.lower() == "4 wheel drive":
                    output["drive_train"] = "4WD"
                if feature_name.lower() == "leather seats":
                    output["upholstery"] = "leather"

            # apify.pushData(output)
            print(output)
