import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class Syncer():

    def __init__(self, profile: bool = True, username: str = "", password: str = "", logging: bool = True) -> None:
        options = webdriver.ChromeOptions()
        if not logging:
            options.add_experimental_option(
                'excludeSwitches',
                ['enable-logging']
            )
        if profile:
            options.add_argument(f'--user-data-dir={os.getcwd()}\\profile')
            options.add_argument('--profile-directory=Default')
        self.driver = webdriver.Chrome(
            ChromeDriverManager(log_level=0).install(),
            options=options
        )
        self.username = username
        self.password = password

    def sync(self) -> None:
        self.driver.get("https://read.amazon.com")
        self.login()
        time.sleep(2)
        self.get_books()
        # time.sleep(2000)

    def stop(self):
        self.driver.close()

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
        books = self.driver.find_elements(By.CSS_SELECTOR, "[data-asin]")
        print("Found", len(books), "books")
        for i in range(len(books)):
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "[data-asin]")
                )
            )
            book = self.driver.find_elements(By.CSS_SELECTOR, "[data-asin]")
            asin = book.get_attribute("data-asin")
            print(asin)
            progress = self.get_book(book)
            print(progress)

    def get_book(self, book: WebElement) -> int:
        book.click()

        iframe = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "KindleReaderIFrame"))
        )
        self.driver.switch_to.frame(iframe)
        progress = 0
        footer = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.ID, "kindleReader_footer_message"))
        )
        progress = footer.text.split("%")[0]
        try:
            progress = int(progress)
        except ValueError:
            pass

        self.driver.switch_to.default_content()
        self.driver.back()  # alternative, click kindleReader_button_close
        return progress


syncer = Syncer()
try:
    syncer.sync()
finally:
    syncer.stop()
