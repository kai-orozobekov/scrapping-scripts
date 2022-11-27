import re
import json
import scrapy
import datetime
from scrapy import Selector

# import apify


class CarrosSpider(scrapy.Spider):
    name = "carros"
    download_timeout = 120
    start_urls = [
        "https://carros.com/likoloi-le-likoloi-tse-rekisoang/georgia/tbilisi-st12237/?page=1"
    ]

    def parse(self, response):
        tree = Selector(response)  # create Selector
        data_list = tree.xpath(
            '//div[contains(@class, "post-item-wrapper relative")]/a/@href'
        ).extract()
        link_list = ["https://carros.com" + i for i in data_list]  # detail url list

        yield from response.follow_all(link_list, self.product_detail)

        next_link = tree.xpath('//a[@class="hs-next"]/@href').extract_first()
        if next_link:
            yield response.follow(
                response.url.split("?page=")[0] + next_link, self.parse
            )

    def product_detail(self, response):
        output = {}
        tree = Selector(response)  # create Selector

        # get picture list
        pictures = tree.xpath("//div[@class='slider-thumbnail-item']/@style").extract()
        picture_list = []
        for p in pictures:
            picture = re.findall("url\((.*?)\)", p, re.S)[0]
            if "https://carros.com" not in picture:
                picture = "https://carros.com" + picture
            picture_list.append(picture)
        # Some web pages only have one picture,Need separate parsing
        if not picture_list:
            picture_list = tree.xpath(
                '//div[@class="slider-item active"]/img/@src'
            ).extract()

        # There may be "vin" and "fuel" in a form
        for i in tree.xpath("//div[@class='detail-item']"):
            span = i.xpath("./span/text()").extract()
            value = i.xpath("./b/text()").extract()
            if "vin" in str(span).lower():
                output["vin"] = value[0]
            elif "fuel" in str(span).lower():
                output["fuel"] = value[0]
            # Judge where "odometer" exists,,,Lines 61-73 are the other two places to judge the existence of "odometer"
            elif "km" in str(value).lower() or " mi" in str(value).lower():
                output["odometer_value"] = int(value[0].split(" ")[0])
                output["odometer_unit"] = value[0].split(" ")[1]

        # Judge the other two places where "odometer" exists
        form_five = tree.xpath(
            '//div[@class="detail-item"][5]/b/text()'
        ).extract_first()
        form_seven = tree.xpath(
            '//div[@class="detail-item"][7]/b/text()'
        ).extract_first()
        form_eight = tree.xpath(
            '//div[@class="detail-item"][8]/b/text()'
        ).extract_first()
        # Some web pages have different formats and need to be judged
        if (
            form_five.isdigit()
            and "km" in form_eight.lower()
            or "mi" in form_eight.lower()
        ):
            output["transmission"] = form_seven
            output["odometer_value"] = int(form_eight.split(" ")[0])
            output["odometer_unit"] = form_eight.split(" ")[1]
        elif (
            form_five.isdigit()
            and "km" in form_seven.lower()
            or "mi" in form_seven.lower()
        ):
            output["transmission"] = tree.xpath(
                '//div[@class="detail-item"][6]/b/text()'
            ).extract_first()
            output["odometer_value"] = int(form_seven.split(" ")[0])
            output["odometer_unit"] = form_seven.split(" ")[1]

        # parse detail data
        output["make"] = tree.xpath(
            '//div[@class="detail-item"][3]/b/text()'
        ).extract_first()
        output["model"] = tree.xpath(
            '//div[@class="detail-item"][4]/b/text()'
        ).extract_first()
        output["year"] = int(
            tree.xpath('//div[@class="detail-item"][5]/b/text()').extract_first()
        )
        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "carros.com"
        output["scraped_listing_id"] = re.findall("-p(.*?)/", response.url, re.S)[0]
        output["vehicle_url"] = response.url
        output["picture_list"] = json.dumps(picture_list)
        city = tree.xpath('//div[@class="detail-item"][1]/div/b/text()').extract_first()
        if city:
            output["city"] = city.split(",")[0]
        output["country"] = "Dominican Republic"
        output["price_retail"] = float(
            tree.xpath('//span[@class="price-value"]/text()')
            .extract_first()
            .replace(",", "")
        )
        output["price_wholesale"] = output["price_retail"]
        output["currency"] = tree.xpath(
            '//span[@class="price-symbol"][2]/text()'
        ).extract_first()

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
