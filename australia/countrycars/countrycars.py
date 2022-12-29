import datetime
import json
import scrapy
from scrapy.selector import Selector

# import apify


class CountryCarsSpider(scrapy.Spider):
    name = "countrycars"
    download_timeout = 120
    start_urls = [
        "https://www.countrycars.com.au/centralwest/search.php?fi=0&pcode=C&srch=Search+Cars&makesel=ANY&body=ANY&minprice=0&maxprice=0&modelsel=0&neworused=ANY&location=Z",
    ]

    def parse(self, response):
        # Traverse product links
        product_links = response.xpath('//a[@class="sfbanner"]/@href').getall()
        yield from response.follow_all(
            product_links,
            callback=self.detail,
        )

        # pagination
        page_link = response.xpath('//a[@class="next page-link"]/@href').get()
        if page_link is not None:
            yield response.follow(
                page_link,
                callback=self.parse,
            )

    def detail(self, response):
        output = {}

        output["ac_installed"] = 0
        output["tpms_installed"] = 0

        # scraping info
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "CountryCars"
        output["vehicle_url"] = response.url
        output["country"] = "AU"

        specifications_table_rows = response.xpath(
            '//section[@id="content2"]/table//tr'
        ).getall()
        for row in specifications_table_rows:
            row = Selector(text=row)
            key = row.xpath("//th/text()").get()
            value = row.xpath("//td//text()").get()
            if value is not None:
                key = key.lower()
                value = value.lower()
                if "make" in key:
                    output["make"] = value
                elif "car model" == key or key == "family":
                    output["model"] = value
                elif "car sub model" == key or key == "variant":
                    output["trim"] = value
                elif "car series" == key or key == "series":
                    if "trim" in output:
                        output["trim"] += " " + value
                    else:
                        output["trim"] = value
                elif "body style" in key:
                    output["body_type"] = value
                elif "vin" == key:
                    output["vin"] = value
                elif "year" in key:
                    output["year"] = int(value)
                elif "cylinders" == key:
                    output["engine_cylinders"] = int(value)
                elif "body colour" in key:
                    output["exterior_color"] = value
                elif "odometer" in key:
                    output["odometer_value"] = int(value)
                    output["odometer_unit"] = "km"
                elif "car engine cc" in key or "capacity" == key:
                    output["engine_displacement_value"] = value
                    output["engine_displacement_units"] = "cc"
                elif "fuel type" in key:
                    output["fuel"] = value
                elif "transmission type" in key:
                    output["transmission"] = value
                elif "car engine type" in key:
                    value = value.split(",")

                    if len(value) > 1:
                        output["engine_block_type"] = value[0]
                        if "cylinder" in value[1]:
                            output["engine_cylinders"] = int(
                                value[1].replace("cylinder", "").replace(" ", "")
                            )
                    else:
                        output["engine_block_type"] = value[0]

        if "year" not in output:
            for k in response.url.split("/"):
                if k.isnumeric():
                    output["year"] = int(k)
                    break

        details_table_rows = response.xpath(
            '//section[@id="content1"]/table//tr'
        ).getall()
        for row in details_table_rows:
            row = Selector(text=row)
            key = row.xpath("//th/text()").get()
            value = row.xpath("//td//text()").get()
            if value is not None:
                key = key.lower().replace(":", "")
                value = value.lower()
                if key == "km" and "odometer_value" not in output:
                    output["odometer_value"] = int(value.replace(",", ""))
                    output["odometer_unit"] = "km"
                elif key == "vin" and "vin" not in output:
                    output["vin"] = value
                elif key == "colour" and "exterior_color" not in output:
                    output["exterior_color"] = value
                elif key == "interior":
                    output["interior_color"] = value
                elif key == "adlinx":
                    output["scraped_listing_id"] = value
                elif key == "location":
                    value = value.split(",")
                    output["city"] = value[0]
                    output["state_or_province"] = value[1]

        price = (
            response.xpath("//div[@id='cc-advert-price']/text()")
            .get()
            .strip()
            .replace("$", "")
            .replace(",", "")
        )
        if price.isnumeric():
            output["price_retail"] = float(price)
            output["currency"] = "AUD"

        comments = response.xpath("//section[@id='cc-advert-comments']//text()").get()
        if comments is not None and len(comments) > 5:
            output["vehicle_disclosure"] = comments.strip()

        imgs = response.xpath("//div[@id='ad-images']//div[1]//img/@src").getall()
        for i in range(len(imgs)):
            imgs[i] = "https://www.countrycars.com.au/" + imgs[i]
        output["picture_list"] = json.dumps(imgs)

        features = response.xpath('//section[@id="content3"]').get()
        if features is not None:
            features_list = (
                Selector(text=features).xpath("//table//tr/td//text()").getall()
            )
            for feature in features_list:
                if feature == "Air Conditioning":
                    output["ac_installed"] = 1
            output["vehicle_options"] = ", ".join(features_list)

        # print(output)
        print("\n")
        # apify.pushData(output)
