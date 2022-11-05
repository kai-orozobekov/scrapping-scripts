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

        number_list = tree.xpath(
            '//li[@class="page-item"]/a/text()'
        ).extract()  # page number list
        last_number = max(
            [int(i) for i in number_list if i.isdigit()]
        )  # get last page number
        current_page = int(str(response.url).split("page=")[1])
        pagination_links = [
            response.url.split("page=")[0] + f"page={i}"
            for i in range(int(current_page) + 1, int(last_number + 1))
        ]  # all page link
        if int(current_page) + 1 < int(last_number + 1):
            yield from response.follow_all(pagination_links, self.parse)

    def product_detail(self, response):
        tree = Selector(response)  # create Selector

        country = tree.xpath('//ol[@class="breadcrumb"]/li[2]/a/text()').extract_first()
        make = (
            tree.xpath('//ol[@class="breadcrumb"]/li[4]/a/text()')
            .extract_first()
            .strip()
        )
        form_data = tree.xpath(
            '//div[@class="col-sm-6 col-12"]'
        )  # Form with required data
        model = None
        year = None
        transmission = None
        fuel = None
        odometer_value = None
        odometer_unit = None
        for i in form_data:  # Loop traversal to get data
            key = i.xpath("./div/div[1]/text()").extract_first()
            value = i.xpath("./div/div[2]/text()").extract_first()
            if key == "Model":
                model = value
            elif key == "Year":
                if value.strip() != "":
                    year = int(value.strip())
                else:
                    year = int(i.xpath("./div/div[2]/a/text()").extract_first().strip())
            elif key == "Transmission":
                transmission = value
            elif key == "Fuel Type":
                fuel = value
            elif key == "Mileage":  # It may not be a number, which requires judgment
                if (
                    value.strip().replace(" ", "").isalpha()
                ):  # If this is English, it is judged to be empty
                    odometer_value = None
                else:
                    value = [
                        i for i in list(value) if i.isdigit() or i == "."
                    ]  # 81832(
                    odometer_value = int(float(str("".join(value)).replace(",", "")))
                    if not odometer_value:
                        odometer_value = int(0)
                    odometer_unit = "KM"

        if (
            not model
        ):  # If the form does not have this field,need to get it from elsewhere
            model_span = tree.xpath("//div[@class='row mt-3']/div/span")
            if len(model_span) == 1:
                model = (
                    tree.xpath("//div[@class='row mt-3']/div/span/a/text()")
                    .extract_first()
                    .strip()
                )
            else:  # Judge different situations
                for spa in model_span:
                    model_data = spa.xpath("./a/text()").extract_first().strip()
                    model_data_list = []
                    if model_data == make.lower():
                        continue
                    else:
                        model_data_list.append(model_data)
                    model = " ".join(model_data_list)

        picture_list = tree.xpath(
            "//div[@class='swiper-wrapper']//picture/source/@srcset"
        ).extract()  # picture list
        picture_list = [
            picture.replace("webp", "jpg")
            for picture in picture_list
            if "816x460" in str(picture)
        ]
        city = (
            tree.xpath("//div[@class='col-md-6 col-sm-6 col-6']/h4/span[2]/a/text()")
            .extract_first()
            .strip()
        )
        price = (
            tree.xpath(
                "//div[@class='col-md-6 col-sm-6 col-6 text-end']/h4/span[2]/text()"
            )
            .extract_first()
            .strip()
        )
        price_retail = []
        currency = None
        for p in list(price):  # Price is a string need to process data
            if p == "₦":
                currency = "NGN"
            elif p.isdigit() or p == ".":
                price_retail.append(p)
        if price_retail:
            price_retail = float("".join(price_retail))
        else:
            price_retail = None

        output = {
            "make": make,
            "model": model,
            "year": year,
            "transmission": transmission,
            "fuel": fuel,
            "ac_installed": 0,
            "tpms_installed": 0,
            "scraped_date": datetime.datetime.isoformat(datetime.datetime.today()),
            "scraped_from": "Carmart",
            "scraped_listing_id": str(response.url).split("/")[-1],
            "odometer_value": odometer_value,
            "odometer_unit": odometer_unit,
            "vehicle_url": response.url,
            "picture_list": json.dumps(picture_list),
            "city": city,
            "country": country,
            "price_retail": price_retail,
            "price_wholesale": price_retail,
            "currency": currency,
        }

        # process empty fields
        list1 = []
        list2 = []
        for k, v in output.items():
            if v or v == 0:
                list1.append(k)
                list2.append(v)
        output = dict(zip(list1, list2))

        # yield output
        # apify.pushData(output)
