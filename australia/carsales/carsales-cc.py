import cloudscraper

scraper = cloudscraper.create_scraper()  # returns a CloudScraper instance
# Or: scraper = cloudscraper.CloudScraper()  # CloudScraper inherits from requests.Session
print(
    scraper.get(
        "https://www.carsales.com.au/cars/details/2022-suzuki-vitara-manual-2wd-my22/OAG-AD-21354127/?Cr=0"
    ).text
)  # => "<!DOCTYPE html><html><head>..."
