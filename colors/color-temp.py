import json
import scrapy
import html
import requests
import datetime
import time
# import apify
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class ColorsSpider(scrapy.Spider):
    name = "Colors-data"
    start_urls = ["https://us.search.chipex.com/make"]

    def parse(self, response):
        mmy_links = []
        jsn_makes = json.loads(html.unescape(response.body.decode()))
        for make in jsn_makes:
            models = requests.get(f"https://us.search.chipex.com/model?make={make}")
            jsn_models = models.json()
            if len(jsn_models) > 1 and "All Models" in jsn_models:
                jsn_models.remove("All Models")
            for model in jsn_models:
                session = requests.Session()
                retry = Retry(connect=8, backoff_factor=0.5)
                adapter = HTTPAdapter(max_retries=retry)
                session.mount('http://', adapter)
                session.mount('https://', adapter)

                years = session.get(
                    f"https://us.search.chipex.com/year?make={make}&model={model}"
                )
                jsn_years = years.json()
                for year in jsn_years:
                    mmy_links.append(
                        f"https://us.search.chipex.com/paint?make={make}&model={model}&year={year}"
                    )

        for link in mmy_links:
            output = {}
            output["scraped_date"] = datetime.datetime.isoformat(
                    datetime.datetime.today()
                )
            colors_data = requests.get(link)
            colors_json = colors_data.json()
            colors = []
            for color in colors_json:  
                make = color["make"]
                output["make"] = make
                model = color["model"]
                output["model"] = model
                year = color["year"]
                output["year"] = year
                output["chipex_id"] = color["id"]
                output["chipex_url"] = f"https://chipex.com/pages/registration-lookup/{make}?type=mmy&Manufacturer={make}&Model={model}&Year={year}".replace(
                    " ", "%20"
                )
                color_obj = {}             
                color_obj["hex"] = color["hex"]
                color_obj["color_name"] = color["name"]
                colors.append(color_obj)

            output["color_data"] = colors
            # apify.pushData(output)
