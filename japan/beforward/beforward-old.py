import datetime
import json

import scrapy

# import apify


class BeforwardjpSpider(scrapy.Spider):
    name = "beforwardjp"
    download_timeout = 120

    def start_requests(self):
        urls = [
            "https://www.beforward.jp/stocklist/page=1/sortkey=n/stock_country=47",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        # Traverse product links
        product_links = response.xpath('//p[@class="make-model"]/a/@href').getall()
        yield from response.follow_all(product_links, self.detail)

        # pagination
        page_link = response.xpath('//a[@class="pagination-next"]/@href').get()
        if page_link is not None:
            yield response.follow(page_link, self.parse)

    def detail(self, response):

        output = {}

        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "BeForward"
        output["scraped_listing_id"] = response.url.split("/")[-2]
        output["country"] = "JP"
        output["city"] = response.xpath(
            '//*[@id="spec"]/div[1]/div[2]/span[2]/b/text()'
        ).get()
        if (
            response.xpath('//span[@class="price ip-usd-price"]/text()').get()
            is not None
        ):
            output["price_retail"] = float(
                response.xpath('//span[@class="price ip-usd-price"]/text()')
                .get()
                .replace("$", "")
                .replace(",", "")
                .strip()
            )
            output["currency"] = "USD"
            output["make"] = response.xpath('//*[@id="bread"]/li[2]/a/text()').get()
            output["model"] = response.xpath('//*[@id="bread"]/li[4]/a/text()').get()

            # description head
            des_key = response.xpath('//td[@class="specs-pickup-text"]/text()').getall()
            des_value = response.xpath(
                '//td[@class="pickup-specification-text"]/text()'
            ).getall()

            for i in range(1, int(len(des_key) / 2 + 1)):
                if des_key[i].strip() == "Mileage" and des_value[i].strip() != "-":
                    if "mile" in des_value[i]:
                        output["odometer_value"] = int(
                            des_value[i].replace(",", "").replace("mile", "").strip()
                        )
                        output["odometer_unit"] = "mile"
                    elif "km" in des_value[i]:
                        output["odometer_value"] = int(
                            des_value[i].replace(",", "").replace("km", "").strip()
                        )
                        output["odometer_unit"] = "km"

                elif des_key[i].strip() == "Year" and des_value[i].strip() != "-":
                    output["year"] = int(des_value[i].split("/")[0].strip())

                elif des_key[i].strip() == "Engine" and des_value[i].strip() != "-":
                    output["engine_displacement_value"] = (
                        des_value[i].replace("cc", "").replace(",", "").strip()
                    )
                    output["engine_displacement_units"] = "cc"

                elif des_key[i].strip() == "Fuel" and des_value[i].strip() != "-":
                    output["fuel"] = des_value[i].strip()

            output["transmission"] = response.xpath(
                '//*[@id="spec"]/table/tr[8]/td[1]/text()'
            ).get()
            output["vehicle_url"] = response.url
            img = response.xpath(
                '//div[@class="list-detail-left list-detail-left-renewal"]/div[@id="gallery"]/ul/li/a/img/@src'
            ).getall()
            for i in range(len(img)):
                img[i] = "https:" + img[i]
            output["picture_list"] = json.dumps(img)

            # process empty fields
            list1 = []
            list2 = []
            for k, v in output.items():
                if v or v == 0:
                    list1.append(k)
                    list2.append(v)
            output = dict(zip(list1, list2))
            # apify.pushData(output)
            # yield output
