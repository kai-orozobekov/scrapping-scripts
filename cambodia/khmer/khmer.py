import gc
import json
import scrapy
import datetime
from scrapy.http.response import Response

# import apify


class Khmer24Spider(scrapy.Spider):
    name = "khmer24"
    start_urls = ["https://www.khmer24.com/en/cars/all-cars.html?"]
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"

    max_req = {}  # Storage required retry link
    max_retry = 5  # retry count

    def start_requests(self):
        for link in self.start_urls:
            yield scrapy.Request(
                url=link,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_context": datetime.datetime.isoformat(
                        datetime.datetime.today()
                    ),
                },
                errback=self.errback_close_page,
            )

    async def parse(self, response: Response):
        page = response.meta["playwright_page"]
        await page.context.close()  # close the context
        await page.close()
        del page
        gc.collect()

        product_links = response.xpath("//a[@class='border post']//@href").getall()
        for link in product_links:
            yield scrapy.Request(
                url=link,
                callback=self.detail,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_context": datetime.datetime.isoformat(
                        datetime.datetime.today()
                    ),
                },
                # errback=self.errback_close_page,
            )

        next_button = response.xpath("//a[@rel='next']/@href").get()
        if next_button:
            yield scrapy.Request(
                url=next_button,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_context": datetime.datetime.isoformat(
                        datetime.datetime.today()
                    ),
                },
                # errback=self.errback_close_page,
            )

    async def detail(self, response):
        page = response.meta["playwright_page"]
        await page.context.close()  # close the context
        await page.close()
        del page
        gc.collect()

        output = {}

        form_data = response.xpath("//ul[@class='list-unstyled item-fields']/li")
        for data in form_data:
            key = data.xpath("./div/span[1]/text()").get()
            value = data.xpath("./div/span[2]/text()").get()
            if "Makes" in key:
                output["make"] = value
            elif "Model" in key:
                output["model"] = value
            elif "Year" in key:
                if value.isdigit():
                    output["year"] = int(value)
            elif "Fuel" in key:
                output["fuel"] = value
            elif "Transmission" in key:
                output["transmission"] = value

        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "khmer24"
        output["scraped_listing_id"] = response.url.split("-")[-1].replace(".html", "")
        output["vehicle_url"] = response.url
        output["city"] = response.xpath(
            "//span[text()='Locations :']/parent::li/span[2]/text()"
        ).get()
        output["country"] = "KH"
        price = response.xpath(
            '//meta[@property="product:price:amount"]/@content'
        ).get()
        if price:
            output["price_retail"] = float(price)
            output["currency"] = response.xpath(
                '//meta[@property="product:price:currency"]/@content'
            ).get()

        picture_list = response.xpath(
            "//div[@class='owl-stage']/div/div/a/@href"
        ).getall()
        if picture_list:
            output["picture_list"] = json.dumps(picture_list)

        # apify.pushData(output)
        # yield output

    # Method of Retry Request
    async def errback_close_page(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.context.close()  # close the context
        await page.close()
        del page
        gc.collect()

        if (
            not self.max_req.get(failure.request.url)
            or self.max_req.get(failure.request.url) < self.max_retry
        ):
            if "all-cars.html" in failure.request.url:
                yield scrapy.Request(
                    url=failure.request.url,
                    callback=self.parse,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_context": datetime.datetime.isoformat(
                            datetime.datetime.today()
                        ),
                    },
                    errback=self.errback_close_page,
                    dont_filter=True,
                )

            elif "all-cars.html" not in failure.request.url:
                yield scrapy.Request(
                    url=failure.request.url,
                    callback=self.detail,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_context": datetime.datetime.isoformat(
                            datetime.datetime.today()
                        ),
                    },
                    errback=self.errback_close_page,
                    dont_filter=True,
                )
            self.max_req[failure.request.url] = (
                self.max_req.get(failure.request.url, 0) + 1
            )
            if len(self.max_req) >= 30:
                self.remove_success_url()

    def remove_success_url(self, url=None):
        # Clear the url of successful retry
        if self.max_req.get(url):
            del self.max_req[url]

        # Clear the url that failed to retry
        if not url:
            for key in self.max_req.keys():
                if self.max_req.get(key) >= 5:
                    del self.max_req[key]
