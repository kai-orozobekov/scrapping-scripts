import scrapy
import datetime
import json
from scrapy.downloadermiddlewares.retry import get_retry_request

# import apify


class Autochek(scrapy.Spider):
    name = "autochek"
    download_timeout = 120
    start_urls = [
        "https://autochek.africa/en/ug/cars-for-sale?country=ug&page_number=1"
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
            car_media = page_props["carMediaList"]
            pictures = [item["url"] for item in car_media]
            pictures.append(car["imageUrl"])

            output = {
                "vin": car.get("vin"),
                "make": car.get("model").get("make").get("name"),
                "model": car.get("model").get("name"),
                "year": int(car.get("year")),
                "transmission": car.get("transmission"),
                "fuel": car.get("fuelType"),
                "ac_installed": 0,
                "tpms_installed": 0,
                "scraped_date": datetime.datetime.isoformat(datetime.datetime.today()),
                "scraped_from": "AutoChek",
                "scraped_listing_id": str(car.get("id")),
                "odometer_value": int(car.get("mileage")),
                "odometer_unit": car.get("mileageUnit"),
                "vehicle_url": response.url,
                "picture_list": json.dumps(pictures),
                "city": car.get("city"),
                "price_retail": float(car.get("marketplacePrice")),
                "currency": page_props.get("country").get("currency"),
            }

            if page_props.get("country").get("country") == "Uganda":
                output["country"] = "UG"
            # yield output
            # apify.pushData(output)
