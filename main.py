import time
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


class Syncer():

    def __init__(self, profile: bool, username: str, password: str) -> None:
        options = webdriver.ChromeOptions()
        if profile:
            options.add_argument(f'--user-data-dir={os.getcwd()}\\profile')
            options.add_argument('--profile-directory=Default')
        self.driver = webdriver.Chrome(
            ChromeDriverManager().install(),
            options=options
        )
        self.username = username
        self.password = password

    def sync(self) -> None:
        self.driver.get("https://read.amazon.com")
        self.login()
        time.sleep(2)
        self.get_books()
        time.sleep(2000)

    def login(self) -> None:
        email_field = self.driver.find_elements(By.ID, "ap_email")
        if email_field:
            email_field = email_field[0]
            password_field = self.driver.find_element(By.ID, "ap_password")
            submit_button = self.driver.find_element(By.ID, "signInSubmit")

            email_field.send_keys(self.username)
            password_field.send_keys(self.password)
            submit_button.click()
            time.sleep(10)

    def get_books(self) -> None:
        for book in self.driver.find_elements(By.CSS_SELECTOR, "[data-asin]"):
            asin = book.get_attribute("data-asin")
            prit(asin)
        # kindleReader_footer_message
