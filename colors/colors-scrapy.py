import json
import scrapy
import html
import datetime

# import apify


class ColorsSpider(scrapy.Spider):
    name = "Colors-data"
    download_timeout = 120
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
    start_urls = ["https://us.search.chipex.com/make"]
    scraped_mmy_links = set()

    def parse(self, response):
        jsn_makes = json.loads(html.unescape(response.body.decode()))
        for make in jsn_makes:
            yield scrapy.Request(
                f"https://us.search.chipex.com/model?make={make}",
                callback=self.get_models,
            )

    def get_models(self, response):
        make = response.url.split("make=")[1]
        jsn_models = json.loads(html.unescape(response.body.decode()))
        if len(jsn_models) > 1 and "All Models" in jsn_models:
            jsn_models.remove("All Models")
        for model in jsn_models[:4]:
            yield scrapy.Request(
                f"https://us.search.chipex.com/year?make={make}&model={model}",
                callback=self.get_years,
                meta={"make": make},
            )

    def get_years(self, response):
        make = response.meta["make"]
        model = response.url.split("model=")[1]
        jsn_years = json.loads(html.unescape(response.body.decode()))
        for year in jsn_years[:4]:
            yield scrapy.Request(
                f"https://us.search.chipex.com/paint?make={make}&model={model}&year={year}",
                callback=self.get_color_data,
                meta={"make": make, "model": model},
            )

    def get_color_data(self, response):
        make = response.meta["make"]
        model = response.meta["model"]
        year = response.url.split("year=")[1]

        output = {}
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["make"] = make
        output["model"] = model
        output["year"] = year
        output[
            "chipex_url"
        ] = f"https://chipex.com/pages/registration-lookup/{make}?type=mmy&Manufacturer={make}&Model={model}&Year={year}".replace(
            " ", "%20"
        )

        if output["chipex_url"] not in self.scraped_mmy_links:
            colors = []
            jsn_color_data = json.loads(html.unescape(response.body.decode()))
            for color in jsn_color_data:
                output["chipex_id"] = color["id"]
                color_obj = {}
                color_obj["hex"] = color["hex"]
                color_obj["color_name"] = color["name"]
                colors.append(color_obj)

            output["color_data"] = colors

            self.scraped_mmy_links.add(output["chipex_url"])
        # apify.pushData(output)
