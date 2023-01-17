import asyncio
from pyppeteer import launch


async def main():
    # launch chromium browser in the background
    browser = await launch()
    # open a new tab in the browser
    page = await browser.newPage()
    # add URL to a new page and then open it
    await page.goto(
        " https://www.carsales.com.au/cars/details/2016-hyundai-tucson-30-special-edition-auto-awd-my17/OAG-AD-21017349/?Cr=8"
    )
    # create a screenshot of the page and save it
    await page.screenshot({"path": "python.png"})
    # close the browser
    await browser.close()


print("Starting...")
asyncio.get_event_loop().run_until_complete(main())
print("Screenshot has been taken")
