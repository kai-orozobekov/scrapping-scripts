import scrapy
import datetime
import json

# import apify


class CarsCom(scrapy.Spider):
    name = "CarsCom"
    download_timeout = 120
    base_url = "https://www.cars.com/shopping/results/?dealer_id=&keyword=&list_price_max=&list_price_min=&maximum_distance=all&mileage_max=&page_size=50&sort=best_match_desc&stock_type=all&year_max=&year_min=&zip=14174"

    def start_requests(self):
        yield scrapy.Request(
            url=self.base_url,
            callback=self.parse_makes,
        )

    def parse_makes(self, response):
        makes = response.xpath("//select[@id='make_select']//option/text()").getall()
        make_urls = []
        for make in makes:
            if make != "All makes":
                make_urls.append(
                    {"link": f"{self.base_url}&makes[]={make}", "make": make}
                )

        for url in make_urls:
            yield response.follow(
                url["link"],
                meta={"make": url["make"]},
                callback=self.parse_models,
            )

    def parse_models(self, response):
        make = response.meta["make"]
        models = response.xpath("//div[@id='model']//label/text()").getall()
        model_urls = []
        for model in models:
            model_urls.append(
                {
                    "link": f"{self.base_url}&makes[]={make}&models[]={make}-{model.strip().replace(' ', '_')}",
                    "model": model.strip(),
                }
            )

        for url in model_urls:
            yield response.follow(
                url["link"],
                meta={"make": make, "model": url["model"]},
                callback=self.parse_trims,
            )

    def parse_trims(self, response):
        make = response.meta["make"]
        model = response.meta["model"]
        trims = response.xpath("//div[@id='trim']//label/text()").getall()

        if len(trims) > 0:
            trim_urls = []
            for trim in trims:
                trim_urls.append(
                    {
                        "link": f"{self.base_url}&makes[]={make}&models[]={make}-{model.replace(' ', '_')}&trims[]={make}-{model.replace(' ', '_')}-{trim.strip().replace(' ', '_').replace('/', '_')}",
                        "trim": trim.strip(),
                    }
                )

            for url in trim_urls:
                yield response.follow(
                    url["link"],
                    meta={"make": make, "model": model, "trim": url["trim"]},
                    callback=self.parse,
                )
        else:
            yield response.follow(
                response.url,
                callback=self.parse,
                meta={"make": make, "model": model},
            )

    def parse(self, response):
        make = response.meta["make"]
        model = response.meta["model"]
        meta = {"make": make, "model": model}

        if "trim" in response.meta:
            trim = response.meta["trim"]
            meta["trim"] = trim

        link_list = response.xpath(
            "//a[@class='vehicle-card-link js-gallery-click-link']/@href"
        ).getall()
        for link in link_list:
            yield response.follow(
                "https://www.cars.com" + link,
                callback=self.detail,
                meta=meta,
            )

        next_link = response.xpath('//a[@aria-label="Next page"]/@href').get()
        if next_link:
            yield response.follow(
                "https://www.cars.com" + next_link,
                callback=self.parse,
                meta={"make": make, "model": model},
            )

    def detail(self, response):
        output = {}

        # scraping info
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "CarsCom"
        output["vehicle_url"] = response.url

        output["ac_installed"] = 0
        output["tpms_installed"] = 0

        # basic info
        make = response.meta["make"]
        output["make"] = make
        model = response.meta["model"]
        output["model"] = model
        title = response.xpath("//h1[@class='listing-title']/text()").get()
        year = title.split(" ")[0]
        if year.isnumeric():
            output["year"] = int(year)

        basics_keys = response.xpath(
            "//section[@class='sds-page-section basics-section']//dt/text()"
        ).getall()
        basics_values_raw = response.xpath(
            "//section[@class='sds-page-section basics-section']//dd/text()"
        ).getall()
        basics_values = list(filter(lambda v: v != "\n", basics_values_raw))
        for i in range(len(basics_keys)):
            key = basics_keys[i].strip().lower()
            value = basics_values[i].strip()
            if value not in ("-", ""):
                if key == "exterior color":
                    output["exterior_color"] = value
                elif key == "interior color":
                    output["interior_color"] = value
                elif key == "drivetrain":
                    output["drive_train"] = value
                elif key == "fuel type":
                    output["fuel"] = value
                elif key == "transmission":
                    output["transmission"] = value
                elif key == "vin":
                    output["vin"] = value
                elif key == "mileage":
                    value = value.split(" ")
                    if value[0].replace(",", "").isnumeric():
                        output["odometer_value"] = int(value[0].replace(",", ""))
                        output["odometer_unit"] = "mi"

        features = response.xpath(
            "//ul[@class='sds-list sds-list--unordered all-features-list']//li//text()"
        ).getall()
        for feature in features:
            if feature in ("A/C", "Air Conditioning"):
                output["ac_installed"] = 1
            elif feature in (
                "Leather seat upholstery",
                "Leather Upholstery",
                "Leather Seats",
            ):
                output["upholstery"] = "leather"

        if "trim" in response.meta:
            output["trim"] = response.meta["trim"]
        else:
            trim = title.replace(make, "").replace(model, "").replace(year, "").strip()
            if len(trim) > 0:
                output["trim"] = trim

        # pricing details
        price = response.xpath("//span[@class='primary-price']/text()").get()
        msrp_price = response.xpath("//span[@class='secondary-price']/text()").get()

        if price is not None and price.lower() != "not priced":
            output["price_retail"] = float(price.replace("$", "").replace(",", ""))
            output["currency"] = "USD"

        if msrp_price is not None and "msrp" in msrp_price.lower():
            output["msrp"] = float(
                price.replace("$", "").replace(",", "").replace("MSRP", "").strip()
            )

        # other info
        condition = response.xpath("//p[@class='new-used']/text()").get()
        if condition is not None:
            if condition.lower() == "used":
                output["is_used"] = 1
            elif condition.lower() == "new":
                output["is_used"] = 0

        # pictures list
        picture_list = response.xpath("//gallery-slides//img/@data-src").getall()

        if picture_list:
            output["picture_list"] = json.dumps(picture_list)

        print(output)
        print("\n")
