import gc
import json
import scrapy
import datetime
from scrapy.http.response import Response

import apify


class LoozapSpider(scrapy.Spider):
    name = 'loozap'
    start_urls = ['https://ug.loozap.com/search?type=1&c=1&page=1']
    max_req = {}  # Storage required retry link
    max_retry = 5  # retry count

    def start_requests(self):
        yield scrapy.Request(
            url=self.start_urls[0],
            callback=self.parse,
            meta={
                "playwright": True, 
                "playwright_include_page": True, 
                "playwright_context": datetime.datetime.isoformat(datetime.datetime.today())
                },
            errback=self.errback_close_page,
        )

    async def parse(self, response: Response):
        page = response.meta["playwright_page"]
        await page.context.close()  # close the context
        await page.close()
        del page
        gc.collect()        

        # Delete successful links on "max_req",  Reduce memory usage
        self.remove_success_url(response.url)

        product_links = response.xpath('//*[@id="postsList"]/div[@class="item-list"]//h5/a/@href').getall()
        for link in product_links:
            yield scrapy.Request(
                url=link,
                callback=self.detail,
                meta={
                    "playwright": True, 
                    "playwright_include_page": True,
                     "playwright_context": datetime.datetime.isoformat(datetime.datetime.today())
                     },
                errback=self.errback_close_page,

            )

        next_button = response.xpath('//a[@aria-label="Next »"]/@href').get()
        if next_button:
            yield scrapy.Request(
                url=next_button,
                callback=self.parse,
                meta={
                    "playwright": True, 
                    "playwright_include_page": True, 
                    "playwright_context": datetime.datetime.isoformat(datetime.datetime.today())
                    },
                errback=self.errback_close_page,
            )

    async def detail(self, response):
        page = response.meta["playwright_page"]
        await page.context.close()  # close the context
        await page.close()
        del page
        gc.collect()

        output = {}
        # Delete successful links on "max_req",  Reduce memory usage
        self.remove_success_url(response.url)

        form_data = response.xpath("//div[@class='row bg-light rounded py-2 mx-0']")
        for data in form_data:
            key = data.xpath("./div[@class='col-6 fw-bolder']/text()").get()
            value = data.xpath("./div[@class='col-6 text-sm-end text-start']/text()").get()
            if not key:
                continue
            if "Brand" in key:
                output["make"] = value
            elif "Model" in key:
                output["model"] = value
            elif "Transmission" in key:
                output["transmission"] = value
            elif "fuel" in key:
                output["fuel"] = value
            elif "Mileage" in key:
                output["odometer_value"] = int(value)

        # Resolve year field in title
        title = response.url.split('/')[4]
        year = "".join([i for i in title.split("-") if len(i) == 4 and i.isdigit() and int(i) > 1950])
        if year:
            output["year"] = int(year)

        # Resolve engine field and fuel field in description
        description = response.xpath('//div[@class="col-12 detail-line-content"]/p/text()').getall()
        for desc in description:
            desc = desc.lower()
            if "enginecc:" in desc or "engine:" in desc:
                engine = desc.split(":")[1].replace("cc", "").replace(",", "").strip()
                if engine.isdigit() and len(engine) == 4:
                    output["engine_displacement_value"] = engine
                    output["engine_displacement_units"] = "cc"
            elif "fuel" in desc and desc and not output.get("fuel"):
                if "fuel:" in desc:
                    output["fuel"] = desc.split(":")[1].strip()
                elif desc.split(" ") == 2 and desc.split(" ")[0] == "fuel":
                    output["fuel"] = desc.split(" ")[1].strip()

        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "Loozap"
        output["scraped_listing_id"] = response.url.split("/")[-1].replace(".html", "")
        output["vehicle_url"] = response.url
        output["country"] = "UG"

        # Parse location and price
        local_and_price = response.xpath("//h4[@class='fw-normal p-0']")
        for j in local_and_price:
            key = j.xpath('./span[@class="fw-bold"]/text()').get()
            if "Location" in key:
                output["city"] = j.xpath('./span/a/text()').get().split(",")[0].strip()
            elif "Price" in key:
                price = j.xpath('./span[2]/text()').get()
                if price:
                    true_price = price.strip().split(" ")[0].replace(",", "")
                    if true_price.isdigit():
                        output["price_retail"] = float(true_price)
                        if price.strip().split(" ")[1].upper() == "USH":
                            output["currency"] = "UGX" 

        picture_list = response.xpath('//div[@class="bxslider"]//img/@src').getall()
        if picture_list:
            output["picture_list"] = json.dumps(picture_list)
            
        apify.pushData(output)
        # yield output
		

    # Method of Retry Request
    async def errback_close_page(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.context.close()  # close the context
        await page.close()
        del page
        gc.collect()

        if not self.max_req.get(failure.request.url) or self.max_req.get(failure.request.url) < self.max_retry:
            if "page=" in failure.request.url:
                yield scrapy.Request(
                    url=failure.request.url,
                    callback=self.parse,
                    meta={
                        "playwright": True, 
                        "playwright_include_page": True, 
                        "playwright_context": datetime.datetime.isoformat(datetime.datetime.today())
                        },
                    errback=self.errback_close_page,
                    dont_filter=True
                )

            elif "page=" not in failure.request.url:
                yield scrapy.Request(
                    url=failure.request.url,
                    callback=self.detail,
                    meta={"playwright": True, 
                    "playwright_include_page": True, 
                    "playwright_context": datetime.datetime.isoformat(datetime.datetime.today())
                    },
                    errback=self.errback_close_page,
                    dont_filter=True

                )
            self.max_req[failure.request.url] = self.max_req.get(failure.request.url, 0) + 1
            if len(self.max_req) >=30:
                self.remove_success_url()
    def remove_success_url(self, url):
        # Clear the url of successful retry
        if self.max_req.get(url):
            del self.max_req[url]

        # Clear the url that failed to retry
        if not url:
            for key in self.max_req.keys():
                if self.max_req.get(key) >= 5:
                    del self.max_req[key]
