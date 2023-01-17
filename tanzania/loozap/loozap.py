import datetime
import json
import scrapy

# import apify


class LoozapSpider(scrapy.Spider):
    name = "Loozap"
    download_timeout = 120
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
    start_urls = [
        "https://tz.loozap.com/category/autos-cars-vehicles-and-trucks/used-cars-new-cars?page=1"
    ]

    def parse(self, response):
        # Traverse product links
        product_links = response.xpath(
            '//*[@id="postsList"]/div[@class="item-list"]//h5/a/@href'
        ).getall()
        for link in product_links:
            yield response.follow(
                link,
                callback=self.detail,
            )

        # pagination
        page_link = response.xpath('//a[@aria-label="Next »"]/@href').get()
        if page_link is not None:
            yield response.follow(
                page_link,
                callback=self.parse,
            )

    def detail(self, response):
        output = {}

        form_data = response.xpath("//div[@class='row bg-light rounded py-2 mx-0']")
        for data in form_data:
            key = data.xpath("./div[@class='col-6 fw-bolder']/text()").get()
            value = data.xpath(
                "./div[@class='col-6 text-sm-end text-start']/text()"
            ).get()
            if not key:
                continue
            if "Brand" in key:
                output["make"] = value
            elif "Model" in key:
                output["model"] = value
            elif "Transmission" in key:
                if value != "Other":
                    output["transmission"] = value
            elif "fuel" in key:
                output["fuel"] = value
            elif "Mileage" in key:
                output["odometer_value"] = int(value)
            elif "Year" in key:
                output["registration_year"] = value
            elif "Mileage" in key:
                output["odometer_value"] = int(value)
                output["odometer_unit"] = "km"
            elif "Condition" in key:
                if value.lower() == "used":
                    output["is_used"] = 1
                elif value.lower() == "new":
                    output["is_used"] = 0

        # Resolve engine field and fuel field in description
        description = response.xpath(
            '//div[@class="col-12 detail-line-content"]/p/text()'
        ).getall()
        if len(description) > 0:
            output["vehicle_disclosure"] = " ".join(description)

        output["ac_installed"] = 0
        output["tpms_installed"] = 0

        # scraping info
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "Loozap"
        output["scraped_listing_id"] = response.url.split("/")[-1].replace(".html", "")
        output["vehicle_url"] = response.url
        output["country"] = "TZ"

        # Parse location and price
        local_and_price = response.xpath("//h4[@class='fw-normal p-0']")
        for j in local_and_price:
            key = j.xpath('./span[@class="fw-bold"]/text()').get()
            if "Location" in key:
                location_array = j.xpath("./span/a/text()").get().split(",")
                output["state_or_province"] = location_array[0].strip()
                if len(location_array) > 1:
                    output["city"] = location_array[1].strip()
            elif "Price" in key:
                price = j.xpath("./span[2]/text()").get()
                if price:
                    true_price = price.strip().split(" ")[0].replace(",", "")
                    if true_price.isdigit():
                        output["price_retail"] = float(true_price)
                        output["currency"] = "TZS"

        picture_list = response.xpath('//div[@class="bxslider"]//img/@src').getall()
        if picture_list:
            output["picture_list"] = json.dumps(picture_list)

        # apify.pushData(output)
        # print(output)
