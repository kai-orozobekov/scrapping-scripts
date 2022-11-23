import scrapy
import datetime
import json

# import apify


class Mercado(scrapy.Spider):
    name = "mercado"
    download_timeout = 120
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
    start_urls = [
        "https://autos.mercadolibre.com.mx/_NoIndex_True_VEHICLE*BODY*TYPE_452759#applied_filter_id%3DVEHICLE_BODY_TYPE%26applied_filter_name%3DTipo+de+carrocer%C3%ADa%26applied_filter_order%3D11%26applied_value_id%3D452759%26applied_value_name%3DSUV%26applied_value_order%3D11%26applied_value_results%3D17016%26is_custom%3Dfalse",
        "https://autos.mercadolibre.com.mx/_NoIndex_True_VEHICLE*BODY*TYPE_452758#applied_filter_id%3DVEHICLE_BODY_TYPE%26applied_filter_name%3DTipo+de+carrocer%C3%ADa%26applied_filter_order%3D11%26applied_value_id%3D452758%26applied_value_name%3DSed%C3%A1n%26applied_value_order%3D10%26applied_value_results%3D15654%26is_custom%3Dfalse",
        "https://autos.mercadolibre.com.mx/_NoIndex_True_VEHICLE*BODY*TYPE_479344#applied_filter_id%3DVEHICLE_BODY_TYPE%26applied_filter_name%3DTipo+de+carrocer%C3%ADa%26applied_filter_order%3D11%26applied_value_id%3D479344%26applied_value_name%3DHatchback%26applied_value_order%3D6%26applied_value_results%3D7836%26is_custom%3Dfalse",
        "https://autos.mercadolibre.com.mx/_NoIndex_True_VEHICLE*BODY*TYPE_452756#applied_filter_id%3DVEHICLE_BODY_TYPE%26applied_filter_name%3DTipo+de+carrocer%C3%ADa%26applied_filter_order%3D11%26applied_value_id%3D452756%26applied_value_name%3DPick-Up%26applied_value_order%3D9%26applied_value_results%3D4020%26is_custom%3Dfalse",
        "https://autos.mercadolibre.com.mx/_NoIndex_True_VEHICLE*BODY*TYPE_452749#applied_filter_id%3DVEHICLE_BODY_TYPE%26applied_filter_name%3DTipo+de+carrocer%C3%ADa%26applied_filter_order%3D11%26applied_value_id%3D452749%26applied_value_name%3DCoup%C3%A9%26applied_value_order%3D3%26applied_value_results%3D2712%26is_custom%3Dfalse",
        "https://autos.mercadolibre.com.mx/_NoIndex_True_VEHICLE*BODY*TYPE_452755#applied_filter_id%3DVEHICLE_BODY_TYPE%26applied_filter_name%3DTipo+de+carrocer%C3%ADa%26applied_filter_order%3D11%26applied_value_id%3D452755%26applied_value_name%3DVan%26applied_value_order%3D14%26applied_value_results%3D960%26is_custom%3Dfalse",
        "https://autos.mercadolibre.com.mx/_NoIndex_True_VEHICLE*BODY*TYPE_452750#applied_filter_id%3DVEHICLE_BODY_TYPE%26applied_filter_name%3DTipo+de+carrocer%C3%ADa%26applied_filter_order%3D11%26applied_value_id%3D452750%26applied_value_name%3DFurgoneta%26applied_value_order%3D5%26applied_value_results%3D642%26is_custom%3Dfalse",
        "https://autos.mercadolibre.com.mx/_NoIndex_True_VEHICLE*BODY*TYPE_452748#applied_filter_id%3DVEHICLE_BODY_TYPE%26applied_filter_name%3DTipo+de+carrocer%C3%ADa%26applied_filter_order%3D11%26applied_value_id%3D452748%26applied_value_name%3DConvertible%26applied_value_order%3D2%26applied_value_results%3D546%26is_custom%3Dfalse",
        "https://autos.mercadolibre.com.mx/_NoIndex_True_VEHICLE*BODY*TYPE_452753#applied_filter_id%3DVEHICLE_BODY_TYPE%26applied_filter_name%3DTipo+de+carrocer%C3%ADa%26applied_filter_order%3D11%26applied_value_id%3D452753%26applied_value_name%3DMinivan%26applied_value_order%3D7%26applied_value_results%3D312%26is_custom%3Dfalse",
    ]

    def parse(self, response):
        # traverse vehicle links
        for link in response.xpath(
            "//div[@class='ui-search-result__image shops__picturesStyles']/a/@href"
        ).getall():
            if link:
                yield response.follow(link, callback=self.detail)

        next_page = response.xpath("//a[@title='Siguiente']/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def detail(self, response):
        output = {}

        # make, model, fuel, transmission, odometer_value, odometer_unit
        map = {
            "Marca": "make",
            "Modelo": "model",
            "Año": "year",
            "Tipo de combustible": "fuel",
            "Transmisión": "transmission",
            "Motor": "engine_displacement_value",
            "Kilómetros": "odometer_value",
            "Tipo de carrocería": "body_type",
            "Puertas": "doors",
            "Color": "exterior_color",
        }

        keys = response.xpath("//tr[@class='andes-table__row']/th/text()").getall()
        values = response.xpath(
            "//tr[@class='andes-table__row']/td/span/text()"
        ).getall()

        for k in map.keys():
            for i in range(len(keys)):
                if k == keys[i]:
                    output[map[k]] = values[i]

        if output.get("odometer_value"):
            output["odometer_unit"] = output["odometer_value"].split(" ")[-1]
            output["odometer_value"] = int(output["odometer_value"].split(" ")[0])

        if output.get("doors"):
            output["doors"] = int(output["doors"])

        if output.get("year"):
            output["year"] = int(output["year"])

        # location details
        keys = response.xpath(
            "//h3[@class='ui-seller-info__status-info__title ui-vip-seller-profile__title']/text()"
        ).getall()
        values = response.xpath(
            "//p[@class='ui-seller-info__status-info__subtitle']/text()"
        ).getall()
        for i in range(len(keys)):
            if keys[i] == "Ubicación del vehículo":
                location = values[i].split("-")
                output["city"] = location[0 if len(location) == 2 else 1].strip()
                output["state_or_province"] = location[
                    1 if len(location) == 2 else 2
                ].strip()
        output["country"] = "Mexico"

        output["ac_installed"] = 0
        output["tpms_installed"] = 0

        # scraping info
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "Mercado Libre"
        output["scraped_listing_id"] = response.url.split("/")[3].split("-")[1]
        output["vehicle_url"] = response.url

        # pictures list
        output["picture_list"] = json.dumps(
            response.xpath(
                "//figure[@class='ui-pdp-gallery__figure']/img/@data-zoom"
            ).getall()
        )

        # pricing details
        output["price_retail"] = float(
            response.xpath("//span[@class='andes-money-amount__fraction']/text()")
            .get()
            .replace("$", "")
            .replace(",", "")
            .strip()
        )
        output["currency"] = "MXN"

        output["vehicle_disclosure"] = " ".join(
            response.xpath("//p[@class='ui-pdp-description__content']/text()").extract()
        )

        # process empty fields
        list1 = []
        list2 = []
        for k, v in output.items():
            if v or v == 0:
                list1.append(k)
                list2.append(v)
        output = dict(zip(list1, list2))

        # apify.pushData(output)
        print(output)
