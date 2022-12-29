import json
import datetime
import re

import scrapy
from scrapy import Selector, Request


# import apify


class AutosusadosSpider(scrapy.Spider):
    name = "AutosUsados"
    start_urls = [
        "https://www.autosusados.cl/Autos.aspx?catid=1&transmision=-1&anoh=0&Base=1,3&regionid=1",
        "https://www.autosusados.cl/Autos.aspx?catid=1&transmision=-1&anoh=0&Base=1,3&regionid=2",
        "https://www.autosusados.cl/Autos.aspx?catid=1&transmision=-1&anoh=0&Base=1,3&regionid=3",
        "https://www.autosusados.cl/Autos.aspx?catid=1&transmision=-1&anoh=0&Base=1,3&regionid=4",
        "https://www.autosusados.cl/Autos.aspx?catid=1&transmision=-1&anoh=0&Base=1,3&regionid=5",
        "https://www.autosusados.cl/Autos.aspx?catid=1&transmision=-1&anoh=0&Base=1,3&regionid=6",
        "https://www.autosusados.cl/Autos.aspx?catid=1&transmision=-1&anoh=0&Base=1,3&regionid=7",
        "https://www.autosusados.cl/Autos.aspx?catid=1&transmision=-1&anoh=0&Base=1,3&regionid=8",
        "https://www.autosusados.cl/Autos.aspx?catid=1&transmision=-1&anoh=0&Base=1,3&regionid=9",
        "https://www.autosusados.cl/Autos.aspx?catid=1&transmision=-1&anoh=0&Base=1,3&regionid=10",
        "https://www.autosusados.cl/Autos.aspx?catid=1&transmision=-1&anoh=0&Base=1,3&regionid=11",
        "https://www.autosusados.cl/Autos.aspx?catid=1&transmision=-1&anoh=0&Base=1,3&regionid=12",
        "https://www.autosusados.cl/Autos.aspx?catid=1&transmision=-1&anoh=0&Base=1,3&regionid=13",
        "https://www.autosusados.cl/Autos.aspx?catid=1&transmision=-1&anoh=0&Base=1,3&regionid=14",
        "https://www.autosusados.cl/Autos.aspx?catid=1&transmision=-1&anoh=0&Base=1,3&regionid=15",
        "https://www.autosusados.cl/Autos.aspx?catid=1&transmision=-1&anoh=0&Base=1,3&regionid=16",
        "https://www.autosusados.cl/Suv.aspx?catid=3&transmision=-1&anoh=0&Base=1,3&regionid=1",
        "https://www.autosusados.cl/Suv.aspx?catid=3&transmision=-1&anoh=0&Base=1,3&regionid=2",
        "https://www.autosusados.cl/Suv.aspx?catid=3&transmision=-1&anoh=0&Base=1,3&regionid=3",
        "https://www.autosusados.cl/Suv.aspx?catid=3&transmision=-1&anoh=0&Base=1,3&regionid=4",
        "https://www.autosusados.cl/Suv.aspx?catid=3&transmision=-1&anoh=0&Base=1,3&regionid=5",
        "https://www.autosusados.cl/Suv.aspx?catid=3&transmision=-1&anoh=0&Base=1,3&regionid=6",
        "https://www.autosusados.cl/Suv.aspx?catid=3&transmision=-1&anoh=0&Base=1,3&regionid=7",
        "https://www.autosusados.cl/Suv.aspx?catid=3&transmision=-1&anoh=0&Base=1,3&regionid=8",
        "https://www.autosusados.cl/Suv.aspx?catid=3&transmision=-1&anoh=0&Base=1,3&regionid=9",
        "https://www.autosusados.cl/Suv.aspx?catid=3&transmision=-1&anoh=0&Base=1,3&regionid=10",
        "https://www.autosusados.cl/Suv.aspx?catid=3&transmision=-1&anoh=0&Base=1,3&regionid=11",
        "https://www.autosusados.cl/Suv.aspx?catid=3&transmision=-1&anoh=0&Base=1,3&regionid=12",
        "https://www.autosusados.cl/Suv.aspx?catid=3&transmision=-1&anoh=0&Base=1,3&regionid=13",
        "https://www.autosusados.cl/Suv.aspx?catid=3&transmision=-1&anoh=0&Base=1,3&regionid=14",
        "https://www.autosusados.cl/Suv.aspx?catid=3&transmision=-1&anoh=0&Base=1,3&regionid=15",
        "https://www.autosusados.cl/Suv.aspx?catid=3&transmision=-1&anoh=0&Base=1,3&regionid=16",
    ]
    city_list = [
        "Tarapaca",
        "Antofagasta",
        "Atacama",
        "Coquimbo",
        "Valparaíso",
        "del Libertador Gral. Bernardo Ohiggins",
        "del Maule",
        "del BioBio",
        "de la Araucania",
        "de los Lagos",
        "Aysén del Gral. Carlos Ibáñez del Campo",
        "Magallanes",
        "Metropolitana",
        "Los Ríos",
        "Arica y Parinacota",
        "Ñuble",
    ]

    def start_requests(self):
        for url in self.start_urls:
            num = int(re.findall("regionid=(\d+)", url)[0])
            yield Request(url, meta={"city": self.city_list[num - 1]})

    def parse(self, response):
        sel = Selector(response)
        div_list = sel.xpath('//div[@id="ResultadoAuto"]')
        for div in div_list:
            url = "https://www.autosusados.cl/" + div.xpath("./a/@href").get()
            car = div.xpath(".//h3/a/text()").get()
            yield Request(
                url,
                meta={"vehicle_url": url, "car": car, "city": response.meta["city"]},
                callback=self.get_data,
            )

        # next page
        next_href = sel.xpath('//a[@aria-label="Next"]/@href').get()
        if next_href:
            url = "https://www.autosusados.cl/" + next_href
            yield Request(url, meta={"city": response.meta["city"]})

    def get_data(self, response):
        sel = Selector(response)

        output = {}

        # defualt
        output["vehicle_url"] = str(response.meta["vehicle_url"])
        output["scraped_listing_id"] = re.findall(
            "\d+", response.meta["vehicle_url"].split("&")[2]
        )[0]
        output["make"] = response.meta["car"].split(" ")[0]
        output["city"] = response.meta["city"]
        try:
            output["model"] = " ".join(response.meta["car"].split(" ")[1:]).strip()
        except IndexError:
            pass
        output["ac_installed"] = 0
        output["tpms_installed"] = 0
        output["country"] = "CL"
        output["scraped_from"] = "Autos Usados"
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        ####### by NT
        vehicle_characteristics = sel.xpath(
            '//span[@id="dCaracteristicas"]//li/text()'
        ).getall()
        for i in vehicle_characteristics:
            if i == "Aire Acondicionado":
                output["ac_installed"] = 1
            if "Puertas" in i:
                output["doors"] = int(i.split(" ")[0])

        if (
            "Sin Datos" not in sel.xpath('//span[@id="dDescripcion"]/text()').get()
        ):  ## By NT
            output["vehicle_disclosure"] = sel.xpath(
                '//span[@id="dDescripcion"]/text()'
            ).get()  ##By NT
        elif (
            "Sin Datos" in sel.xpath('//span[@id="dDescripcion"]/text()').get()
        ):  # By NT
            output["vehicle_disclosure"] = ""  # By NT

        output["exterior_color"] = sel.css("span#dColor::text").get()
        ########

        # get picture
        picture = sel.xpath('//a[@data-fancybox="images"]/@href').getall()
        if picture:
            output["picture_list"] = json.dumps(picture)

        # get price
        price = "".join(sel.css("span#dPrecio::text").re("[0-9]"))
        if price:
            output["price_retail"] = float(price)
            output["currency"] = "CLP"

        if sel.css("span#dTransmicion::text").get():  ## By NT
            if "Sin Datos" not in sel.css("span#dTransmicion::text").get():  ## By NT
                output["transmission"] = sel.css(
                    "span#dTransmicion::text"
                ).get()  ## By NT
            elif "Sin Datos" in sel.css("span#dTransmicion::text").get():  ## By NT
                output["transmission"] = ""  ## By NT

        if (
            sel.css("span#dAno::text").get()
            and sel.css("span#dAno::text").get().strip().isdigit()
        ):
            output["year"] = int(sel.css("span#dAno::text").get())

        if sel.css("span#dKms::text").get():
            # output['odometer_value'] = int(''.join(sel.css('span#dKms::text').re('[0-9]')))
            output["odometer_unit"] = "km"

        if sel.css("span#dCombustible::text").get():
            output["fuel"] = sel.css("span#dCombustible::text").get()

        # # apify.pushData(output)
        # yield output
        # print(output)
