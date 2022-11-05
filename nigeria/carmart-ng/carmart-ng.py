import scrapy
import json
import datetime
from scrapy import Selector

# import apify


class CarmartSpider(scrapy.Spider):
    name = "carmart"
    download_timeout = 120
    start_urls = ["https://carmart.ng/cars-for-sale?c=1&q=&location=&l=&r=&page=1"]

    def parse(self, response):
        tree = Selector(response)  # create Selector
        data_list = tree.xpath('//div[@id="postsList"]/div')
        link_list = [
            i.xpath('.//h5[@class="add-title"]/a/@href').extract_first()
            for i in data_list
        ]  # detail url list
        yield from response.follow_all(link_list, self.product_detail)

        # page number list
        number_list = tree.xpath('//li[@class="page-item"]/a/text()').extract()

        # get last page number
        last_number = max([int(i) for i in number_list if i.isdigit()])

        current_page = int(str(response.url).split("page=")[1])

        # all page link
        pagination_links = [
            response.url.split("page=")[0] + f"page={i}"
            for i in range(int(current_page) + 1, int(last_number + 1))
        ]

        if int(current_page) + 1 < int(last_number + 1):
            yield from response.follow_all(pagination_links, self.parse)

    def product_detail(self, response):
        # create Selector
        tree = Selector(response)
        output = {}

        # location
        output["country"] = tree.xpath(
            '//ol[@class="breadcrumb"]/li[2]/a/text()'
        ).extract_first()
        output["city"] = (
            tree.xpath("//div[@class='col-md-6 col-sm-6 col-6']/h4/span[2]/a/text()")
            .extract_first()
            .strip()
        )

        output["make"] = (
            tree.xpath('//ol[@class="breadcrumb"]/li[4]/a/text()')
            .extract_first()
            .strip()
        )

        # Table with vehicle data
        keys = tree.xpath("//tbody//th/text()").getall()
        filtered_values = list(
            filter(
                lambda value: value != "\n", tree.xpath("//tbody//td//text()").getall()
            )
        )
        values = [element.replace("\n", "") for element in filtered_values]

        for i in range(len(keys)):
            if keys[i] == "Year":
                output["year"] = int(values[i])
            elif keys[i] == "Fuel Type":
                output["fuel"] = values[i]
            elif keys[i] == "Transmission":
                output["transmission"] = values[i]
            elif "model" in keys[i].lower():
                output["model"] = values[i]
            elif keys[i] == "Mileage":
                mileage_value = values[i].replace(",", "")
                if mileage_value.isnumeric():
                    output["odometer_value"] = int(mileage_value)
                    output["odometer_unit"] = "km"
                elif "K" in mileage_value or "k" in mileage_value:
                    mileage_value = mileage_value.replace("K", "")
                    mileage_value = int(mileage_value) * 1000
                    output["odometer_value"] = int(mileage_value)
                    output["odometer_unit"] = "km"
            elif keys[i] == "Condition":
                condition = values[i]
                if "used" in condition.lower() or "tokunbo" == condition.lower():
                    output["is_used"] = 1
                else:
                    output["is_used"] = 0

        filtered_features = list(
            filter(
                lambda value: value != "\n",
                tree.xpath(
                    "//li[contains(@class, 'col-md-4') and contains(@class, 'ps-1')]/text()"
                ).getall(),
            )
        )
        features = [element.replace("\n", "").strip() for element in filtered_features]
        output["ac_installed"] = 0
        if "Air conditionar" in features:
            output["ac_installed"] = 1

        # pictures
        pictures = tree.xpath(
            "//div[@class='swiper-wrapper']//picture/source/@srcset"
        ).extract()
        picture_list = [
            picture.replace("webp", "jpg")
            for picture in pictures
            if "816x460" in str(picture)
        ]
        output["picture_list"] = json.dumps(picture_list)

        # description
        description = response.xpath(
            "//div[contains(@class, 'col-12') and contains(@class, 'detail-line-content')]//text()"
        ).getall()
        output["vehicle_disclosure"] = "\n".join(
            list(filter(lambda value: value != "\n", description))
        )

        # price details
        price = (
            tree.xpath(
                "//div[@class='col-md-6 col-sm-6 col-6 text-end']/h4/span[2]/text()"
            )
            .extract_first()
            .strip()
            .replace("₦", "")
            .replace(",", "")
        )

        if price.isnumeric():
            output["price_retail"] = float(price)
            output["currency"] = "NGN"

        output["tpms_installed"] = 0
        # scrapping data
        output["scraped_from"] = "Carmart"
        output["scraped_listing_id"] = str(response.url).split("/")[-1]
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["vehicle_url"] = response.url

        # process empty fields
        list1 = []
        list2 = []
        for k, v in output.items():
            if v or v == 0:
                list1.append(k)
                list2.append(v)
        output = dict(zip(list1, list2))

        if "price_retail" in output:
            pass
            # apify.pushData(output)
