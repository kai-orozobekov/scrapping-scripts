import scrapy
import json
import datetime

# import apify


class MotorsSpider(scrapy.Spider):
    name = "motors"
    download_timeout = 120
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
        "x-trademe-uniqueclientid": "58c9bf47-e8b8-5a82-be30-8f5377812cba",
        "referer": "https://www.trademe.co.nz/",
    }

    def start_requests(self):
        urls = [
            "https://api.trademe.co.nz/v1/search/general.json?page=1&rows=22&return_canonical=true&return_metadata=true&return_ads=true&return_empty_categories=true&return_super_features=true&return_did_you_mean=true&canonical_path=%2Fmotors%2Fcars&return_variants=true&auto_category_jump=false&snap_parameters=true",
        ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                headers=self.headers,
                cb_kwargs={"page": 1},
            )

    def parse(self, response, page):
        jsn = response.json()
        if jsn["List"] != []:
            print(jsn["List"])
            print("\n\n")
            for des in jsn["List"]:
                output = {}
                output["ac_installed"] = 0
                output["tpms_installed"] = 0
                output["scraped_date"] = datetime.datetime.isoformat(
                    datetime.datetime.today()
                )
                output["scraped_from"] = "TradeMe Motors"
                output["scraped_listing_id"] = str(des["ListingId"])
                output["country"] = "NZ"
                output["price_retail"] = float(des["StartPrice"])
                output["currency"] = "NZD"
                output["year"] = int(des["Year"])
                output["make"] = des["Make"]
                output["model"] = des["Model"]
                output["transmission"] = des["Transmission"]
                output["fuel"] = des["Fuel"]
                output["city"] = des["Region"]
                output["odometer_value"] = int(des["Odometer"])
                output["odometer_unit"] = "km"
                output["engine_displacement_value"] = des["EngineSize"]
                output["engine_displacement_units"] = "cc"
                output["vin"] = des["Vin"]
                output["exterior_color"] = des["ExteriorColour"]  ## by NT
                output["body_type"] = des["BodyStyle"]  ## by NT
                output["doors"] = des["Doors"]  ## by NT
                output["state_or_province"] = des["Suburb"]  ## by NT
                if des["Is4WD"] == True:  ## by NT
                    output["drive_train"] = "4x4"  ## by NT

                output["vehicle_url"] = (
                    "https://www.trademe.co.nz/a" + des["CanonicalPath"]
                )
                img = []
                try:
                    for i in des["PhotoUrls"]:
                        img.append(i)
                except Exception:
                    pass
                if img != []:
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

            # pagination
            page += 1
            page_link = f"https://api.trademe.co.nz/v1/search/general.json?page={page}&rows=22&return_canonical=true&return_metadata=true&return_ads=true&return_empty_categories=true&return_super_features=true&return_did_you_mean=true&canonical_path=%2Fmotors%2Fcars&return_variants=true&auto_category_jump=false&snap_parameters=true"
            yield response.follow(
                url=page_link,
                callback=self.parse,
                headers=self.headers,
                cb_kwargs={"page": page},
            )
