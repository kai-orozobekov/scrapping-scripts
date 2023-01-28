import datetime
import json
import scrapy
from translate import Translator

# import apify


class PolovniSpider(scrapy.Spider):
    name = "PolovniAutomobili"
    download_timeout = 120
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
    start_urls = [
        "https://www.polovniautomobili.com/auto-oglasi/pretraga?page=2&sort=basic&city_distance=0&showOldNew=all&without_price=1",
    ]
    translator = Translator(from_lang="sr", to_lang="en")

    def parse(self, response):
        # Traverse product links
        product_links = response.xpath('//a[@class="ga-title"]/@href').getall()
        for link in product_links:
            yield response.follow(
                "https://www.polovniautomobili.com" + link,
                callback=self.detail,
            )

        # pagination
        page_link = response.xpath('//a[@class="js-pagination-next"]/@href').get()
        if page_link is not None:
            yield response.follow(
                "https://www.polovniautomobili.com" + page_link,
                callback=self.parse,
            )

    def detail(self, response):
        output = {}

        output["ac_installed"] = 0
        output["tpms_installed"] = 0

        # scraping info
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "PolovniAutomobili"
        output["vehicle_url"] = response.url

        # location details
        output["country"] = "RS"

        price_data = response.xpath(
            '//span[@class="priceClassified regularPriceColor"]//text()'
        ).get()
        if price_data is not None:
            price = (
                price_data.replace(".", "").replace(",", "").replace("€", "").strip()
            )
            if price.isnumeric():
                output["price_retail"] = float(price)
                output["currency"] = "EUR"

        description = response.xpath(
            '//div[@class="uk-width-1-1 description-wrapper"]//text()'
        ).get()
        if description is not None:
            output["vehicle_disclosure"] = self.translator.translate(
                description.strip()
            )

        pictures = response.xpath('//ul[@id="image-gallery"]//li/img/@src').getall()
        if len(pictures) > 0:
            output["picture_list"] = json.dumps(pictures)

        general_info_keys = response.xpath(
            '//div[@class="infoBox"]//div[@class="uk-grid"]//div[@class="uk-width-1-2"]/text()'
        ).getall()
        general_info_values = response.xpath(
            '//div[@class="infoBox"]//div[@class="uk-grid"]//div[@class="uk-width-1-2 uk-text-bold"]/text()'
        ).getall()

        for i in range(len(general_info_values)):
            key = general_info_keys[i].lower()
            value = general_info_values[i].lower()
            if "stanje" == key:
                if value == "polovno vozilo":
                    output["is_used"] = 1
                elif value == "novo vozilo":
                    output["is_used"] = 0
            elif "marka" == key:
                output["make"] = value
            elif "model" == key:
                output["model"] = value
            elif "godište" == key:
                output["year"] = int(value.replace(".", ""))
            elif "kilometraža" == key:
                mileage_data = value.split(" ")
                output["odometer_value"] = int(mileage_data[0].replace(".", ""))
                output["odometer_unit"] = mileage_data[1]
            elif "karoserija" == key:
                output["body_type"] = self.translator.translate(value)
            elif "gorivo" == key:
                output["fuel"] = self.translator.translate(value)
            elif "kubikaža" == key:
                output["engine_displacement_value"] = value.split(" ")[0]
                output["engine_displacement_units"] = value.split(" ")[1]
            elif "broj oglasa:" == key:
                output["scraped_listing_id"] = value
            elif "broj šasije:" == key:
                output["chassis_number"] = value
            elif "boja" == key:
                output["exterior_color"] = self.translator.translate(value)
            elif "materijal enterijera" == key:
                upholstery = self.translator.translate(value)
                if "A ... cloth?" == upholstery:
                    output["upholstery"] = "cloth"
                else:
                    output["upholstery"] = upholstery
            elif "boja enterijera" == key:
                output["interior_color"] = self.translator.translate(value)
            elif "broj sedišta" == key:
                if value.split(" ")[0].isnumeric():
                    output["seats"] = int(value.split(" ")[0])
            elif "broj vrata" == key:
                if value.split("/")[0].isnumeric():
                    output["doors"] = int(value.split("/")[0])
            elif "pogon" == key:
                output["drive_train"] = value
            elif "menjač" == key:
                output["transmission"] = self.translator.translate(value)
            elif "strana volana" == key:
                output["steering_position"] = self.translator.translate(value)
            elif "klima" == key:
                if value != "nema klimu":
                    output["ac_installed"] = 1

        # apify.pushData(output)
