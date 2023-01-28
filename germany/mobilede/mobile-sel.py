from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36")



driver = webdriver.Chrome(chrome_options=chrome_options)
driver.get("https://www.mobile.de/?lang=en")
driver.find_element(By.XPATH, '//button[@class="sc-bczRLJ iBneUr mde-consent-accept-btn"]').click()
driver.find_element(By.XPATH, '//button[@data-testid="qs-submit-button"]').click()
# driver.find_element(By.XPATH, '//span[@class="recaptcha-checkbox goog-inline-block recaptcha-checkbox-unchecked rc-anchor-checkbox"]').click()



