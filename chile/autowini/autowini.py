import datetime
import json
import scrapy

# import apify


class AutowiniSpider(scrapy.Spider):
    name = "autowini"
    download_timeout = 120

    def start_requests(self):
        urls = [
            "https://www.autowini.com/search/cars?conditions=C020&locations=C0350&status=C030&pageSize=30&pageOffset=0",
        ]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse, cb_kwargs={"page": 0})

    def parse(self, response, page):
        jsn = response.json()
        if jsn["cars"]["resultSet"] != []:
            for car in jsn["cars"]["resultSet"]:
                output = {}
                print(car)

                output["ac_installed"] = 0
                output["tpms_installed"] = 0
                output["scraped_date"] = datetime.datetime.isoformat(
                    datetime.datetime.today()
                )
                output["scraped_from"] = "Autowini"
                output["scraped_listing_id"] = car["listingId"]
                output["country"] = "CL"
                output["make"] = car["makeName"]
                output["model"] = car["modelName"]
                output["year"] = int(car["year"])
                output["fuel"] = car["fuelType"]
                ###### by NT
                output["body_type"] = car["vehicleType"]
                output["steering_position"] = car["steeringType"]
                output["drive_train"] = car["drivetrainType"]
                output["seats"] = int(car["passengerCapacity"])
                ######
                if car["engineVolume"] != "0":
                    output["engine_displacement_value"] = car["engineVolume"]
                    output["engine_displacement_units"] = "cc"
                output["price_retail"] = float(car["itemPrice"])
                output["currency"] = "USD"
                if car["transmissionType"] == "AT":
                    output["transmission"] = "Automatic"
                elif car["transmissionType"] == "MT":
                    output["transmission"] = "Manual"
                elif car["transmissionType"] == "CVT":
                    output["transmission"] = "CVT"

                output["vehicle_url"] = "https://www.autowini.com" + car["detailUrl"]

                img = []
                img.append(car["mainPhotoPath"])
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

            # pagination
            page += 1
            page_link = f"https://www.autowini.com/search/cars?conditions=C020&locations=C0350&status=C030&pageSize=30&pageOffset={page}"
            yield response.follow(
                url=page_link, callback=self.parse, cb_kwargs={"page": page}
            )
