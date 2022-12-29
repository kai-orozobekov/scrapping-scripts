import json

# import apify
import scrapy
import datetime
from translate import Translator


class GuaziSpider(scrapy.Spider):
    name = "guazi"
    start_urls = [
        "https://mapi.guazi.com/car-source/carList/pcList?versionId=0.0.0.0&sourceFrom=wap&deviceId=7d52489b-be0c-4387-801b-7a0f6a0ffa66&osv=Windows+10&minor=&sourceType=&ec_buy_car_list_ab=&location_city=&district_id=&tag=-1&license_date=&auto_type=&driving_type=&gearbox=&road_haul=&air_displacement=&emission=&car_color=&guobie=&bright_spot_config=&seat=&fuel_type=&order=&priceRange=0,-1&tag_types=&diff_city=&intention_options=&initialPriceRange=&monthlyPriceRange=&transfer_num=&car_year=&carid_qigangshu=&carid_jinqixingshi=&cheliangjibie=&page=1&pageSize=20&city_filter=12&city=12&guazi_city=12&qpres=596468335941177344&platfromSource=wap"
    ]

    def __init__(self):
        # City name and city id

        # The encrypted character of the website corresponding to the number
        self.digit_encry = {
            "&#59854": "0",
            "&#58397": "1",
            "&#58928": "2",
            "&#60146": "3",
            "&#58149": "4",
            "&#59537": "5",
            "&#60492": "6",
            "&#57808": "7",
            "&#59246": "8",
            "&#58670": "9",
        }

    def start_requests(self):
        # The website data is displayed by city, so the city ID needs to be traversed
        for city in self.city_data.keys():
            url_module = f"https://mapi.guazi.com/car-source/carList/pcList?versionId=0.0.0.0&sourceFrom=wap&deviceId=7d52489b-be0c-4387-801b-7a0f6a0ffa66&osv=Windows+10&minor=&sourceType=&ec_buy_car_list_ab=&location_city=&district_id=&tag=-1&license_date=&auto_type=&driving_type=&gearbox=&road_haul=&air_displacement=&emission=&car_color=&guobie=&bright_spot_config=&seat=&fuel_type=&order=&priceRange=0,-1&tag_types=&diff_city=&intention_options=&initialPriceRange=&monthlyPriceRange=&transfer_num=&car_year=&carid_qigangshu=&carid_jinqixingshi=&cheliangjibie=&page=1&pageSize=20&city_filter={self.city_data[city]}&city={self.city_data[city]}&guazi_city={self.city_data[city]}&qpres=596468335941177344&platfromSource=wap"
            yield scrapy.Request(
                url=url_module, callback=self.parse, cb_kwargs={"city": city}
            )

    def parse(self, response, city):
        res = json.loads(response.text)  # Get website json data

        jsn = res["data"]["postList"]
        for data in jsn:
            output = {}
            title = data.get("title")  # Parse the required data from the title
            year = [
                i
                for i in title.replace("款", "").split(" ")
                if i.isdigit() and len(i) == 4
            ]
            if (
                year
            ):  # If there is no year field, the car brand and model data cannot be parsed
                output["year"] = int(year[0])

                # make and model
                make_model = title.split(f" {output.get('year')}")[0]
                # Dealing with the combination of car brand and model,,,such as "本田XR-V"
                if len(make_model.split(" ")) == 1:
                    make_model_data = make_model
                    # Match the first string of the vehicle model and use this string to separate the brand and vehicle model
                    split_work = None
                    for i in list(make_model_data):
                        if i.encode("utf-8").isalnum():
                            split_work = i
                            break
                    output["make"] = make_model_data.split(str(split_work))[0]
                    if len(make_model_data.split(str(split_work))) > 1:
                        output["model"] = (
                            str(split_work) + make_model_data.split(str(split_work))[1]
                        )
                    else:
                        output["model"] = None
                else:  # Dealing with the separation of car brands and models,,such as "名爵 锐腾"
                    output["make"] = make_model.split(" ")[0]
                    output["model"] = "".join(make_model.split(" ")[1:])
                    translator = Translator(from_lang="zh", to_lang="en")
                    translation = translator.translate(output["make"])
                    print(translation)

            if output.get("make", "") == "":
                continue

            # engine
            engin_data = [
                i
                for i in title.split(" ")
                if "cc" in i.lower() or "t" in i.lower() or "l" in i.lower()
            ]
            engine = ""
            for eng in engin_data:
                if (
                    "cc" in eng.lower()
                    and eng.lower().replace("cc", "").isdigit()
                    and len(eng.lower().replace("cc", "")) == 4
                ):
                    engine = eng
                elif (
                    "l" in eng.lower()
                    and "." in eng
                    and eng.lower().replace("l", "").replace(".", "").isdigit()
                ):
                    engine = eng
                elif (
                    "t" in eng.lower()
                    and "." in eng
                    and eng.lower().replace("t", "").replace(".", "").isdigit()
                ):
                    engine = eng

            if engine != "":
                output["engine_displacement_value"] = "".join(
                    [i for i in list(engine) if i.isdigit() or i == "."]
                )
                output["engine_displacement_units"] = "".join(
                    [i for i in list(engine) if i.isalpha()]
                )

            # transmission
            if "手动" in title:
                output["transmission"] = "手动"
            elif "自动" in title:
                output["transmission"] = "自动"

            # mileage
            mileage = data.get("road_haul").replace(
                ";", ""
            )  # such as "&#60146;.&#59246;万公里"
            for digit in self.digit_encry.keys():
                if digit in mileage:
                    mileage = mileage.replace(digit, self.digit_encry[digit])
                    # Split data and units
                    odometer_value = "".join(
                        [i for i in list(mileage) if i.isdigit() or i == "."]
                    )
                    odometer_unit = mileage.replace(odometer_value, "")
                    if "万" in odometer_unit:
                        output["odometer_value"] = int(float(odometer_value) * 10000)
                        output["odometer_unit"] = odometer_unit.replace("万", "")
                    else:
                        output["odometer_value"] = int(odometer_value)

            output["ac_installed"] = 0
            output["tpms_installed"] = 0
            output["scraped_date"] = datetime.datetime.isoformat(
                datetime.datetime.today()
            )
            output["scraped_from"] = "guazi"
            output["scraped_listing_id"] = data["clue_id"]
            output["vehicle_url"] = data["wapUrl"].split("&")[0].replace("m.", "")
            picture_list = data.get("thumb_img")
            if picture_list:
                output["picture_list"] = json.dumps([picture_list])

            output["city"] = city
            output["country"] = "CN"
            price = eval(data["service_tracking_info"]).get("price")
            if price:
                output["price_retail"] = float(price)
                output["price_wholesale"] = output["price_retail"]
                output["currency"] = "CNY"

            # process empty fields
            list1 = []
            list2 = []
            for k, v in output.items():
                if v or v == 0:
                    if v != "-":
                        list1.append(k)
                        list2.append(v)
            output = dict(zip(list1, list2))

            # apify.pushData(output)
            # yield output

        last_page = res["data"]["totalPage"]
        current_page = int(res["data"]["page"])
        next_link = response.url.replace(
            f"page={current_page}", f"page={current_page+1}"
        )
        if current_page + 1 < int(last_page) + 1:
            yield scrapy.Request(
                url=next_link, callback=self.parse, cb_kwargs={"city": city}
            )
