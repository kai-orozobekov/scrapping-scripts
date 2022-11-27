import json

# import apify
import scrapy
import datetime


class CarclassicSpider(scrapy.Spider):
    name = "carClassic"
    start_urls = [
        "https://www.carandclassic.com/classic_cars.php?category=3&country=156&sort_1=latest&search"
    ]

    def parse(self, response):
        product_link = response.xpath(
            "//a[contains(@class, 'image') and contains(@class, 'outbound')]/@href"
        ).getall()
        yield from response.follow_all(product_link, self.product_detail)

        next_button = response.xpath("//a[@title='Next']/@href").get()
        if next_button:
            yield response.follow(next_button, self.parse)

    def product_detail(self, response):
        output = {}

        form_data = response.xpath("//table[@class='w-full lg:w-5/12 mb-2']//tr")
        for data in form_data:
            key = data.xpath("./td[1]/text()").get()
            if "Make" in key:
                output["make"] = data.xpath("./td[2]/a/span/text()").get()
            elif data.xpath(".//td[@itemprop='model']"):
                output["model"] = data.xpath("./td[2]/a/text()").get().strip()
            elif "Year" in key:
                year = data.xpath("./td[2]/text()").get()
                if year:
                    output["year"] = int(year)
            elif "Mileage" in key:
                odometer_value = data.xpath("./td[2]/span[1]/text()").get()
                if odometer_value:
                    output["odometer_value"] = int(odometer_value.replace(",", ""))
                    output["odometer_unit"] = (
                        data.xpath("./td[2]/span[2]/text()").get().strip()
                    )
            elif "Town" in key:
                output["city"] = data.xpath("./td[2]/text()").get()
            elif "Country" in key:
                country = data.xpath("./td[2]/a/text()").get().strip()
                if country.lower() == "mexico":
                    output["country"] = "MX"

        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "CarClassic"
        output["scraped_listing_id"] = response.url.split("/").pop()
        output["vehicle_url"] = response.url

        price = response.xpath(
            "//li[@itemprop='offers']//span[@itemprop='price']/@content"
        ).get()
        if price and price.strip().isdigit():
            output["price_retail"] = float(price)
            output["currency"] = response.xpath(
                "//li[@itemprop='offers']//span[@itemprop='priceCurrency']/@content"
            ).get()

        picture_list = response.xpath(
            "//ul[@id='advert-gallery']/li/img/@srcset | //ul[@id='advert-gallery']/li/img/@src"
        ).getall()
        picture_list = [i.split(",").pop() for i in picture_list]
        if picture_list:
            output["picture_list"] = json.dumps(picture_list)

        output["vehicle_disclosure"] = response.xpath(
            "//div[@itemprop='description']/text()"
        ).get()

        # process empty fields
        list1 = []
        list2 = []
        for k, v in output.items():
            if v or v == 0:
                list1.append(k)
                list2.append(v)
        output = dict(zip(list1, list2))

        if "country" in output and output["country"] == "MX":
            pass
            # apify.pushData(output)
