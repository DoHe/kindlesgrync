import os
import time
from dataclasses import dataclass
from typing import Dict, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


@dataclass
class Book:
    title: str
    asin: str
    progress: int
    authors: str


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
        self.collected: Dict[str, Book] = {}

    def sync(self) -> None:
        self.driver.get("https://read.amazon.com")
        self.login()
        self.get_books()

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

    def get_books(self) -> None:
        books = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "[data-asin]")
            )
        )
        print("Found", len(books), "books")
        book_index = 0
        prev_last_asin = ""
        while True:
            books = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "[data-asin]")
                )
            )
            last_asin = books[-1].get_attribute("data-asin")

            book = books[book_index]
            asin, title, authors = self.get_book_attributes(book)
            progress = self.get_progress(book)
            self.collected[asin] = Book(title, asin, progress, authors)
            self.store_collected()

            book_index += 1
            if book_index == len(books):
                if last_asin == prev_last_asin:
                    break
                book_index -= 1
            prev_last_asin = last_asin

    def get_book_attributes(self, book: WebElement) -> Tuple[str, str, str]:
        asin = book.get_attribute("data-asin")
        title = self.driver.find_element(By.ID, "title-" + asin)
        authors = self.driver.find_element(By.ID, "author-" + asin)
        return asin, title.text, authors.text

    def get_progress(self, book: WebElement) -> int:
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
        self.wait_for_text(footer)
        progress = footer.text.split("%")[0]
        try:
            progress = int(progress)
        except ValueError:
            pass
        self.driver.switch_to.default_content()
        time.sleep(1)
        self.driver.back()
        return progress

    def store_collected(self):
        print(self.collected)

    def wait_for_text(self, elem):
        i = 0
        while not elem.text:
            time.sleep(0.5)
            i += 1
            if i > 20:
                break


syncer = Syncer()
try:
    syncer.sync()
finally:
    syncer.stop()
