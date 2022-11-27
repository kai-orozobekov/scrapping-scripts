import scrapy
import datetime
import re

# import apify
from scrapy.http.response import Response

car_brands = [
    "Abarth",
    "AC",
    "Acura",
    "Adler",
    "Alfa Romeo",
    "Alpina",
    "Alpine",
    "AMC",
    "AM General",
    "Ariel",
    "Aro",
    "Asia",
    "Aston Martin",
    "Audi",
    "Aurus",
    "Austin",
    "Austin Healey",
    "Autobianchi",
    "Avtokam",
    "Bajaj",
    "Baltijas Dzips",
    "Batmobile",
    "Bedford",
    "Beijing",
    "Bentley",
    "Bertone",
    "Bilenkin",
    "Bitter",
    "BMW",
    "Bolwell",
    "Borgward",
    "Brabus",
    "Brilliance",
    "Bristol",
    "Bronto",
    "Bufori",
    "Bugatti",
    "Buick",
    "BYD",
    "Byvin",
    "Cadillac",
    "Callaway",
    "Carbodies",
    "Caterham",
    "Chana",
    "Changan",
    "ChangFeng",
    "Chery",
    "Chevlolet",
    "Chevrolet",
    "Chrysler",
    "CHTC",
    "Citroen",
    "Cizeta",
    "Coggiola",
    "Dacia",
    "Dadi",
    "Daewoo",
    "DAF",
    "Daihatsu",
    "Daimler",
    "Datsun",
    "Delage",
    "DeLorean",
    "Derways",
    "DeSoto",
    "De Tomaso",
    "Dodge",
    "DongFeng",
    "Doninvest",
    "Donkervoort",
    "DS",
    "DW Hower",
    "Eagle",
    "Eagle Cars",
    "E-Car",
    "Ecomotors",
    "Excalibur",
    "FAW",
    "Ferrari",
    "Fiat",
    "Fisker",
    "Flanker",
    "Ford",
    "FORD",
    "Foton",
    "FSO",
    "Fuqi",
    "GAC",
    "GAZ",
    "Geely",
    "Genesis",
    "Geo",
    "GMC",
    "Gonow",
    "Gordon",
    "GP",
    "Great Wall",
    "Hafei",
    "Haima",
    "Hanomag",
    "Haval",
    "Hawtai",
    "Hindustan",
    "Hispano-Suiza",
    "Holden",
    "Honda",
    "Horch",
    "HuangHai",
    "Hudson",
    "Hummer",
    "Hyundai",
    "Infiniti",
    "Infinity",
    "Innocenti",
    "Invicta",
    "Iran Khodro",
    "Isdera",
    "Isuzu",
    "IVECO",
    "Izh",
    "JAC",
    "Jaguar",
    "Jeep",
    "Jensen",
    "Jinbei",
    "JMC",
    "Kanonir",
    "Kia",
    "Koenigsegg",
    "Kombat",
    "KTM",
    "Lada",
    "Lamborghini",
    "Lancia",
    "Land Rover",
    "Landwind",
    "Lexus",
    "Liebao Motor",
    "Lifan",
    "Ligier",
    "Lincoln",
    "Lotus",
    "LTI",
    "LUAZ",
    "Lucid",
    "Luxgen",
    "Mahindra",
    "Marcos",
    "Marlin",
    "Marussia",
    "Maruti",
    "Maserati",
    "Maybach",
    "Mazda",
    "McLaren",
    "Mega",
    "Mercedes",
    "Mercedes-Benz",
    "Mercury",
    "Metrocab",
    "MG",
    "Microcar",
    "Minelli",
    "Mini",
    "MINI",
    "Mitsubishi",
    "Mitsuoka",
    "Morgan",
    "Morris",
    "Moskvich",
    "Nash",
    "Nissan",
    "Noble",
    "Oldsmobile",
    "Opel",
    "Osca",
    "Packard",
    "Pagani",
    "Panoz",
    "Perodua",
    "Peugeot",
    "PGO",
    "Piaggio",
    "Plymouth",
    "Pontiac",
    "Porsche",
    "Premier",
    "Proton",
    "PUCH",
    "Puma",
    "Qoros",
    "Qvale",
    "Rambler",
    "Range Rover",
    "Ravon",
    "Reliant",
    "Renaissance",
    "Renault",
    "Renault Samsung",
    "Rezvani",
    "Rimac",
    "Rolls-Royce",
    "Ronart",
    "Rover",
    "Saab",
    "Saipa",
    "Saleen",
    "Santana",
    "Saturn",
    "Scion",
    "SEAT",
    "Shanghai Maple",
    "ShuangHuan",
    "Simca",
    "Skoda",
    "Smart",
    "SMZ",
    "Soueast",
    "Spectre",
    "Spyker",
    "SsangYong",
    "Steyr",
    "Studebaker",
    "Subaru",
    "Suzuki",
    "TagAZ",
    "Talbot",
    "TATA",
    "Tatra",
    "Tazzari",
    "Tesla",
    "Think",
    "Tianma",
    "Tianye",
    "Tofas",
    "Toyota",
    "Trabant",
    "Tramontana",
    "Triumph",
    "TVR",
    "UAZ",
    "Ultima",
    "Vauxhall",
    "VAZ (Lada)c",
    "Vector",
    "Venturi",
    "Volkswagen",
    "Volvo",
    "Vortex",
    "Wanderer",
    "Wartburg",
    "Westfield",
    "Wiesmann",
    "Willys",
    "W Motors",
    "Xin Kai",
    "Yo-mobile",
    "Zastava",
    "ZAZ",
    "Zenos",
    "Zenvo",
    "Zibar",
    "ZIL",
    "ZiS",
    "Zotye",
    "ZX",
    "ВАЗ",
]


class MySpider(scrapy.Spider):
    name = "carros"
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"
    }

    def start_requests(self):
        urls = [
            "https://carros.com/cars-and-automobiles-for-sale-co225/?page=1&range=500",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        product_links = [
            *response.xpath(
                '//div[@class="post-item-wrapper relative secondplan"]/a/@href'
            ).getall(),
            *response.xpath(
                '//div[@class="post-item-wrapper relative firstplan secondplan"]/a/@href'
            ).getall(),
        ]
        yield from response.follow_all(product_links, self.detail)

        # next_link = response.xpath('//a[@data-testid="pagination-forward"]/@href').get()
        # if next_link is not None:
        # yield response.follow(next_link, self.parse)

    def detail(self, response):
        output = {}
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "carros"
        output["country"] = "UA"
        output["vehicle_url"] = response.url
        output["scraped_listing_id"] = response.url.split("-")[-1].strip(" /")
        output["tpms_installed"] = 0
        output["ac_installed"] = 0
        output["engine_displacement_value"] = 0
        output["engine_displacement_unit"] = 0

        data = response.xpath('//div[@class="detail-item"]')
        for i, d in enumerate(data):
            info = " ".join(d.xpath("./descendant::*/text()").getall())
            if i == 0:
                output["city"] = info.split(",")[0].strip()
            elif re.search("Auto|Man", info, re.IGNORECASE) is not None:
                output["transmission"] = info
            elif re.search("km", info, re.IGNORECASE) is not None:
                output["odometer_value"] = int(re.sub("[^0-9]", "", info))
                output["odometer_unit"] = "km"
            elif (
                re.search("([12][0-9][0-9][0-9].*[^a-b])", info, re.IGNORECASE)
                is not None
            ):
                output["year"] = info
            elif info in car_brands:
                output["make"] = info
                output["model"] = " ".join(
                    data[i + 1].xpath("./descendant::*/text()").getall()
                )
            elif re.search("USD", info, re.IGNORECASE) is not None:
                info = re.sub("[^0-9]", "", info)
                output["price_retail"] = float(info)
                output["currency"] = "USD"
            elif re.search("EUR", info, re.IGNORECASE) is not None:
                info = re.sub("[^0-9]", "", info)
                output["price_wholesale"] = info
                output["price_retail"] = float(info)
                output["currency"] = "EUR"
            elif re.search("UAH", info, re.IGNORECASE) is not None:
                info = re.sub("[^0-9]", "", info)
                output["price_wholesale"] = info
                output["price_retail"] = float(info)
                output["currency"] = "UAH"

            elif re.search("vin:", info, re.IGNORECASE) is not None:
                output["vin"] = info.split(":")[-1]

        output["picture_list"] = ",".join(
            [
                *response.xpath('//div[@class="slider-item active"]/img/@src').getall(),
                *response.xpath('//div[@class="slider-item"]/img/@data-src').getall(),
            ]
        )
        # apify.pushData(output)
