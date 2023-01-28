import json
import scrapy
import html
import requests
import datetime


# import apify


class ColorsSpider(scrapy.Spider):
    name = "Colors-data"
    records = []
    download_timeout = 120
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
    start_urls = ["https://us.search.chipex.com/make"]

    def parse(self, response):
        mmy_links = []
        jsn_makes = json.loads(html.unescape(response.body.decode()))
        for make in jsn_makes:
            models = requests.get(f"https://us.search.chipex.com/model?make={make}")
            jsn_models = models.json()
            if len(jsn_models) > 1 and "All Models" in jsn_models:
                jsn_models.remove("All Models")
            for model in jsn_models[:2]:
                years = requests.get(
                    f"https://us.search.chipex.com/year?make={make}&model={model}"
                )
                jsn_years = years.json()
                for year in jsn_years:
                    mmy_links.append(
                        f"https://us.search.chipex.com/paint?make={make}&model={model}&year={year}"
                    )
                    print(len(mmy_links))
            print(make)

        for link in mmy_links:
            colors_data = requests.get(link)
            colors_json = colors_data.json()
            output = {}
            output["scraped_date"] = datetime.datetime.isoformat(
                datetime.datetime.today()
            )

            colors = []
            for color in colors_json:
                color_obj = {}
                color_obj["hex"] = color["hex"]
                color_obj["color_name"] = color["name"]
                colors.append(color_obj)

                make = color["make"]
                output["make"] = make
                model = color["model"]
                output["model"] = model
                year = color["year"]
                output["year"] = year
                output["chipex_id"] = color["id"]
                output[
                    "chipex_url"
                ] = f"https://chipex.com/pages/registration-lookup/{make}?type=mmy&Manufacturer={make}&Model={model}&Year={year}".replace(
                    " ", "%20"
                )

            output["color_data"] = colors
            self.records.append(output)

        with open("data.json", "w", encoding="utf-8") as file:
            json.dump(self.records, file)
