import json
import datetime
import re
from scrapy.selector import Selector
import scrapy


# import apify


class AmotorSpider(scrapy.Spider):
    name = "AMotor"
    start_urls = ["https://www.amotor.cl/autos-usados"]

    def parse(self, response):
        # Traverse product links
        href_list = response.xpath(
            '//section[@class="contenido"]/figure/a[@title="Ver Detalles"]/@href'
        ).getall()
        yield from response.follow_all(href_list, self.detail)

        # pagination
        page_link = response.xpath('//li[@class="next"]/a/@href').get()
        if page_link:
            yield response.follow(url=page_link, callback=self.parse)

    def detail(self, response):
        output = {}

        # defualt
        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        output["country"] = "CL"
        output["scraped_from"] = "A Motor"
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_listing_id"] = response.url.split("/")[-1]
        # get price
        price = response.xpath('//span[@id="item_product_prop"]/@content').get()
        if price:
            output["price_retail"] = float(price)
            output["currency"] = "CLP"  ## by NT

            output["make"] = response.url.split("/")[4]
            output["model"] = response.url.split("/")[5]

            # get detail
            li_list = response.xpath('//ul[@class="keyFacts__list"]/li')
            for i in range(len(li_list)):
                key = (
                    response.xpath(
                        f'//ul[@class="keyFacts__list"]/li[{i + 1}]/img/@src'
                    )
                    .get()
                    .strip()
                )
                value = (
                    response.xpath(f'//ul[@class="keyFacts__list"]/li[{i + 1}]/text()')
                    .get()
                    .strip()
                )
                print(value)
                if "calendar" in key:
                    output["year"] = int(value)

                elif "gas-station" in key:
                    output["fuel"] = value

                elif "gearshift" in key:
                    output["transmission"] = value

                elif "dashboard" in key:
                    try:
                        output["odometer_value"] = int(
                            "".join(re.findall("\d+", value))
                        )
                        output["odometer_unit"] = re.findall("[a-zA-Z]+", value)[0]
                    except (TypeError, IndexError):
                        pass

                # elif 'engine' in key and value:
                #     if value.split(' ')[0] != 0:
                #         output['engine_displacement_value'] = value.split(' ')[0]
                #         if value.split(' ')[1]:
                #             output['engine_displacement_units'] = value.split(' ')[1]

                list_values = response.xpath(
                    '//section[@class="fpaDescription separator detalle-full-primary mob-show"]/text()'
                ).getall()  ## by NT
                converted_list = []  ## by NT
                for element in list_values:  ## by NT
                    converted_list.append(element.strip())  ## by NT

                    try:  ## by NT
                        output["vehicle_disclosure"] = converted_list[1]  ## by NT
                    except IndexError:  ## by NT
                        pass  ## by NT

            checkbox_value = response.xpath(
                '//div[@class ="form-group checkbox checkbox-primary"]'
            ).getall()  ## by NT
            for i in checkbox_value:  ## by NT
                key = (
                    Selector(text=i)
                    .xpath('//input[@type ="checkbox" and @checked]')
                    .get()
                )  ## by NT
                if key is not None:  ## by NT
                    value = (
                        Selector(text=i)
                        .xpath('//label[@class="checkbox-inline"]//text()')
                        .getall()
                    )  ## by NT
                    for j in value:  ## by NT
                        if j == "Airbag delanteros":  ## by NT
                            output["ac_installed"] = 1  ## by NT

        span_list = response.css("div#div-Info span")
        for span in span_list:
            if span.xpath("./strong/text()").get() == "Dirección\nSucursal: ":
                output["city"] = span.xpath("text()").get().split(",")[-2].strip()

        output["vehicle_url"] = response.url
        # get picture
        picture = response.xpath('//img[@class="tracking-standard-link"]/@src').getall()
        if picture:
            output["picture_list"] = json.dumps(picture)

            # apify.pushData(output)
