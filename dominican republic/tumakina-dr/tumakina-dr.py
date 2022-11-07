import scrapy
import json
import datetime
import datetime

# import apify


class TuMakina(scrapy.Spider):
    name = "tumakina"
    download_timeout = 120
    id = 0
    type_list = ["1", "2", "3", "4", "5", "8"]
    start_urls = ["https://tumakina.com/ajax-more.php"]
    headers = {
        "Host": "tumakina.com",
        "Content-Length": "347",
    }
    body = {
        "term": "",
        "type": "",
        "brand": "",
        "model": "",
        "year": "",
        "province": "",
        "sorting": "low",
        "engine": "",
        "gas": "",
        "traction": "",
        "mileage": "",
        "oferta": "0",
        "garantia": "0",
        "piel": "0",
        "asientos": "0",
        "llave": "0",
        "sunroof": "0",
        "camara": "0",
        "pantalla": "0",
        "applecar": "0",
        "asientosfilas": "0",
        "page": "0",
        "currentYear": datetime.datetime.now().strftime("%Y"),
        "price": "",
        "ordenar": "",
        "provincemobile": "",
        "pricemobile": "",
        "marcamoto": "",
        "modelomoto": "",
        "marcamontacargas": "",
        "modelomontacargas": "",
        "marcaplantas": "",
        "modeloplantas": "",
    }

    def start_requests(self):
        type = self.type_list[0]
        del self.type_list[0]
        self.body["type"] = type
        yield scrapy.FormRequest(
            url=self.start_urls[0],
            method="POST",
            headers=self.headers,
            formdata=self.body,
            callback=self.parse,
        )

    def parse(self, response):
        # Traverse product links
        product_links = response.xpath("//div[@class='fila']/a/@href").getall()
        yield from response.follow_all(product_links, callback=self.detail)

        # pagination
        id = response.xpath("//span[@class='show_more']/@id").get()
        data_year = response.xpath("//span[@class='show_more']/@data-year").get()
        if id is not None:
            if id != self.id:
                self.id = id
                self.body["page"] = str(id)
                self.body["currentYear"] = str(data_year)
                yield scrapy.FormRequest(
                    url="https://tumakina.com/ajax-more.php",
                    method="POST",
                    headers=self.headers,
                    formdata=self.body,
                    callback=self.parse,
                )
        # Traverse the next type
        elif len(self.type_list) > 0:
            self.id = 0
            self.body["page"] = "0"
            self.body["currentYear"] = datetime.datetime.now().strftime("%Y")
            type = self.type_list[0]
            del self.type_list[0]
            self.body["type"] = type
            yield scrapy.FormRequest(
                url="https://tumakina.com/ajax-more.php",
                method="POST",
                headers=self.headers,
                formdata=self.body,
                callback=self.parse,
            )

    def detail(self, response):
        output = {}

        make = response.xpath("//span[@id='txtMarca']/text()").get()
        if make is not None:
            output["make"] = make

        model = response.xpath("//span[@id='txtModelo']/text()").get()
        if model is not None:
            output["model"] = model

        model_addition = response.xpath("//span[@class='edicion']/text()").get()
        if model_addition is not None:
            output["model"] = output["model"] + " " + model_addition.strip()

        year = response.xpath("//span[@id='txtAno']/text()").get().replace("\n", "")
        if year is not None and year != "":
            output["year"] = int(year)

        keys = response.xpath("//table/tr").getall()
        for i in range(len(keys)):
            index = i + 1
            key = response.xpath(f"//table/tr[{index}]/td[1]/text()").get()
            if key == "Combustible":
                value = response.xpath(f"//table/tr[{index}]/td[2]/span/text()").get()
            else:
                value = response.xpath(f"//table/tr[{index}]/td[2]//text()").get()

            if value is not None and value != "-":
                value = value.strip()
                if key == "Motor":
                    engine_value = value.split("›")
                    if len(engine_value) == 2:
                        engine_cylinders = engine_value[0].split(" ")[0]
                        if engine_cylinders.isnumeric():
                            output["engine_cylinders"] = engine_cylinders
                        engine_displacement = engine_value[1].strip().split(" ")
                        if (
                            len(engine_displacement) == 2
                            and engine_displacement[1] == "L"
                        ):
                            output["engine_displacement_units"] = engine_displacement[1]
                            output["engine_displacement_value"] = engine_displacement[
                                0
                            ].replace(",", "")

                elif key == "Combustible":
                    output["fuel"] = value

                elif key == "Transmisión":
                    output["transmission"] = value

                elif key == "Tracción":
                    output["drive_train"] = value

                elif key == "Color interior":
                    output["interior_color"] = value

                elif key == "Color exterior":
                    output["exterior_color"] = value

                elif key == "Acabado interior":
                    output["upholstery"] = value

                elif key == "Pasajeros":
                    if value.isnumeric():
                        output["seats"] = int(value)

                elif key == "Uso":
                    if value.lower() == "nuevo":
                        output["is_used"] = 0

        output["ac_installed"] = 0
        output["tpms_installed"] = 0

        # scraping info
        output["scraped_date"] = datetime.datetime.isoformat(datetime.datetime.today())
        output["scraped_from"] = "tuMakina"
        output["scraped_listing_id"] = (
            response.xpath("//div[@class='registro']/text()")
            .get()
            .replace("Reg. No.", "")
            .strip()
        )
        output["vehicle_url"] = response.url

        # pictures list
        pictures = response.xpath("//div[@class='item']/a/@href").getall()
        if len(pictures) == 0:
            pictures.extend(response.xpath("//a[@class='mainphoto ']/@href").get())
        output["picture_list"] = json.dumps(
            ["https://tumakina.com/" + url for url in pictures]
        )

        # location information
        output["state_or_province"] = response.xpath(
            "//span[@class='provincia']/text()"
        ).get()
        output["country"] = "Dominican Republic"

        # dealer name
        output["dealer_name"] = (
            response.xpath("//div[@class='nombredealer']/span/text()").get().strip()
        )

        # pricing details
        price = response.xpath("//div[@class='precio']/text()").getall()[1].strip()
        if price != "":
            if "RD" in price:
                output["currency"] = "RD"
            elif "US" in price:
                output["currency"] = "USD"
            output["price_retail"] = float(
                price.replace("US", "")
                .replace("$", "")
                .replace(",", "")
                .replace("RD", "")
            )

        # process empty fields
        list1 = []
        list2 = []
        for k, v in output.items():
            if v is not None:
                list1.append(k)
                list2.append(v)
        output = dict(zip(list1, list2))

        # apify.pushData(output)
