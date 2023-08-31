#  GET POPULAR MOVIES FROM HOMEPAGE

import csv
import time
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium import webdriver
import chromedriver_autoinstaller

class JustWatchScrape:

    def driver_initialize(self):
        chrome_options = Options()
        ua = UserAgent()
        userAgent = ua.random
        print(userAgent)
        chrome_options.add_argument(f'user-agent={userAgent}')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-browser-side-navigation')
        chrome_options.add_argument("--dns-prefetch-disable")
        chrome_options.add_argument("--disable-javascript")

        # driver = webdriver.Chrome(
        #     executable_path=chromedriver_autoinstaller.install(), chrome_options=chrome_options)
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),options=chrome_options)
        
        driver.set_page_load_timeout(300)
        return driver

    def open_website(self):
        driver.get("https://www.justwatch.com/uk")
        time.sleep(2)

    def scroll_to_bottom(self):
        SCROLL_PAUSE_TIME = 2
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
    def search_movies(self):
        self.scroll_to_bottom()
        with open('justwatch_data_urls.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            links = driver.find_elements(By.XPATH, '//a[@class="title-list-grid__item--link"]')
            for link in links:
                full_link= link.get_attribute('href')
                print(full_link)
                writer.writerow([full_link])
        file.close() 

if __name__ == "__main__":
    driver = webdriver.Chrome()
    justrwatch = JustWatchScrape()
    driver = justrwatch.driver_initialize()
    justrwatch.open_website()
    justrwatch.search_movies()