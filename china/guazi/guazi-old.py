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

    global false, null, true
    false = null = true = ""

    def __init__(self):
        # City name and city id
        self.city_data = {
            "重庆": "15",
            "深圳": "17",
            "上海": "13",
            "成都": "45",
            "广州": "16",
            "北京": "12",
            "合肥": "123",
            "芜湖": "124",
            "马鞍山": "126",
            "安庆": "127",
            "滁州": "128",
            "阜阳": "129",
            "颍上县": "100819",
            "宿州": "130",
            "六安": "132",
            "淮南": "310",
            "淮北": "311",
            "铜陵": "312",
            "黄山": "313",
            "亳州": "314",
            "池州": "315",
            "宣城": "316",
            "綦江": "102859",
            "万州": "102863",
            "涪陵": "102864",
            "黔江": "102865",
            "长寿": "102866",
            "江津": "102868",
            "合川": "102869",
            "永川": "102870",
            "南川": "1002871",
            "奉节": "1002886",
            "石柱": "1002889",
            "福州": "2889",
            "厦门": "76",
            "莆田": "77",
            "三明": "78",
            "泉州": "79",
            "漳州": "80",
            "南平": "81",
            "龙岩": "82",
            "宁德": "83",
            "增城": "1001163",
            "珠海": "17",
            "汕头": "18",
            "佛山": "19",
            "江门": "21",
            "开平": "101199",
            "茂名": "22",
            "惠州": "23",
            "东莞": "23",
            "中山": "24",
            "韶关": "25",
            "湛江": "264",
            "肇庆": "265",
            "梅州": "266",
            "汕尾": "267",
            "海丰": "1001193",
            "河源": "268",
            "阳江": "269",
            "清远": "270",
            "潮州": "271",
            "揭阳": "272",
            "云浮": "273",
            "罗定": "1001144",
            "柳州": "133",
            "桂林": "134",
            "灵川": "1001306",
            "梧州": "135",
            "钦州": "136",
            "贵港": "137",
            "玉林": "138",
            "百色": "139",
            "河池": "140",
            "来宾": "141",
            "南宁": "142",
            "北海": "317",
            "防城港": "318",
            "贺州": "319",
            "崇左": "320",
            "兰州": "166",
            "金昌": "167",
            "白银": "168",
            "天水": "169",
            "武威": "170",
            "张掖": "171",
            "平凉": "172",
            "酒泉": "173",
            "庆阳": "174",
            "定西": "175",
            "陇南": "324",
            "临夏": "325",
            "贵阳": "36",
            "六盘水": "37",
            "遵义": "38",
            "安顺": "39",
            "铜仁": "40",
            "毕节": "41",
            "黔西南": "42",
            "黔东南": "43",
            "黔南": "44",
            "石家庄": "1",
            "唐山": "2",
            "秦皇岛": "3",
            "邯郸": "4",
            "邢台县": "1001812",
            "涿州": "1001686",
            "张家口": "7",
            "承德": "8",
            "沧县": "1001773",
            "三河": "1001731",
            "大厂": "1001737",
            "衡水": "11",
            "郑州": "103",
            "洛阳": "104",
            "平顶山": "105",
            "焦作": "106",
            "鹤壁": "107",
            "新乡": "108",
            "安阳": "109",
            "漯河": "110",
            "南阳": "111",
            "济源": "112",
            "济源市": "100104116",
            "濮阳": "294",
            "开封": "293",
            "许昌": "295",
            "三门峡": "296",
            "商丘": "297",
            "信阳": "298",
            "周口": "299",
            "驻马店": "300",
            "海口": "143",
            "三亚": "144",
            "琼海": "377",
            "武汉": "194",
            "黄石": "195",
            "大冶": "1002291",
            "襄阳": "196",
            "十堰": "197",
            "荆州": "198",
            "宜昌": "199",
            "钟祥": "1002260",
            "鄂州": "201",
            "仙桃": "202",
            "潜江": "203",
            "孝感": "327",
            "黄冈": "328",
            "咸宁": "329",
            "咸安": "1002155",
            "恩施": "331",
            "天门": "332",
            "神农架": "333",
            "长沙": "204",
            "株洲": "205",
            "湘潭": "206",
            "衡阳": "207",
            "邵阳": "208",
            "岳阳": "209",
            "常德": "210",
            "郴州": "211",
            "永州": "212",
            "娄底": "213",
            "张家界": "334",
            "益阳": "335",
            "怀化": "336",
            "湘西": "337",
            "哈尔滨": "93",
            "齐齐哈尔": "94",
            "甘南": "1003173",
            "鸡西": "95",
            "鹤岗": "96",
            "双鸭山": "97",
            "大庆": "98",
            "伊春": "99",
            "佳木斯": "100",
            "黑河": "101",
            "绥化": "102",
            "七台河": "301",
            "牡丹江": "302",
            "大兴安岭": "303",
            "长春": "84",
            "吉林": "85",
            "四平": "86",
            "辽源": "87",
            "通化": "88",
            "白山": "89",
            "松原": "90",
            "白城": "91",
            "延边": "92",
            "南京": "65",
            "无锡": "66",
            "苏州": "67",
            "昆山": "1001564",
            "徐州": "68",
            "常州": "69",
            "南通": "70",
            "连云港": "71",
            "淮安": "72",
            "盐城": "73",
            "扬州": "74",
            "镇江": "290",
            "丹阳": "101581",
            "泰州": "291",
            "宿迁": "292",
            "南昌": "214",
            "景德镇": "215",
            "萍乡": "216",
            "九江": "217",
            "新余": "218",
            "鹰潭": "219",
            "赣州": "220",
            "南康": "101664",
            "吉安": "221",
            "宜春": "222",
            "抚州": "223",
            "上饶": "224",
            "沈阳": "55",
            "大连": "56",
            "鞍山": "57",
            "抚顺": "58",
            "丹东": "59",
            "锦州": "60",
            "营口": "61",
            "辽阳": "62",
            "盘锦": "63",
            "葫芦岛": "64",
            "本溪": "286",
            "阜新": "287",
            "铁岭": "288",
            "朝阳": "289",
            "呼和浩特": "145",
            "包头": "146",
            "乌海": "147",
            "赤峰": "148",
            "通辽": "149",
            "鄂尔多斯": "150",
            "呼伦贝尔": "151",
            "巴彦淖尔": "152",
            "临河": "100391",
            "乌兰察布": "153",
            "乌兰浩特": "100354",
            "锡林郭勒": "321",
            "银川": "165",
            "石嘴山": "339",
            "吴忠": "340",
            "固原": "341",
            "中卫": "342",
            "西宁": "186",
            "海东": "187",
            "都江堰": "100587",
            "大邑": "100596",
            "自贡": "46",
            "泸州": "47",
            "德阳": "48",
            "绵阳": "49",
            "乐山": "50",
            "南充": "51",
            "宜宾": "52",
            "达州": "53",
            "凉山": "54",
            "攀枝花": "274",
            "广元": "275",
            "遂宁": "276",
            "内江": "277",
            "广安": "278",
            "眉山": "279",
            "雅安": "280",
            "巴中": "281",
            "资阳": "282",
            "阿坝": "283",
            "济南": "113",
            "青岛": "114",
            "淄博": "115",
            "枣庄": "116",
            "滕州": "100872",
            "东营": "117",
            "烟台": "118",
            "潍坊": "119",
            "威海": "120",
            "滨州": "122",
            "邹平": "100912",
            "济宁": "304",
            "泰安": "305",
            "日照": "日照",
            "莒县": "100866",
            "临沂": "307",
            "德州": "308",
            "聊城": "309",
            "菏泽": "338",
            "太原": "155",
            "大同": "156",
            "阳泉": "157",
            "长治": "158",
            "晋城": "159",
            "朔州": "160",
            "晋中": "161",
            "运城": "162",
            "忻州": "163",
            "临汾": "164",
            "吕梁": "323",
            "西安": "176",
            "铜川": "177",
            "宝鸡": "178",
            "咸阳": "179",
            "渭南": "180",
            "延安": "181",
            "汉中": "182",
            "榆林": "183",
            "安康": "184",
            "商洛": "8",
            "商州": "1002907",
            "天津": "14",
            "乌鲁木齐": "241",
            "昌吉市": "1001441",
            "伊犁": "252",
            "昆明": "225",
            "曲靖": "226",
            "玉溪": "227",
            "保山": "228",
            "昭通": "229",
            "丽江": "230",
            "普洱": "231",
            "临沧": "232",
            "文山": "233",
            "文山市": "100250",
            "红河": "234",
            "西双版纳": "235",
            "楚雄": "236",
            "大理": "237",
            "德宏": "238",
            "怒江": "239",
            "迪庆": "240",
            "桐庐": "1002072",
            "宁波": "27",
            "温州": "28",
            "嘉兴": "28",
            "湖州": "29",
            "长兴": "1002088",
            "安吉": "102089",
            "绍兴": "31",
            "金华": "32",
            "衢州": "33",
            "舟山": "34",
            "台州": "35",
            "温岭": "102036",
            "临海": "102037",
            "玉环": "102038",
            "丽水": "285",
            "东阳": "1002110",
        }
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
