import os
import time
import json
from typing import List, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from constants import STORE_PATH, COLLECTED

BLOCKED = [
    "My life in Sarawak"
]


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
        self.collected: COLLECTED = {}

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

    def wait_for_books(self) -> List[WebElement]:
        return WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "[data-asin]")
            )
        )

    def get_books(self) -> None:
        books = self.wait_for_books()
        total_num_books = self.scroll_to_index(-1)
        print("Found", total_num_books, "books total")
        book_index = self.restore_collected()
        while True:
            books = self.wait_for_books()
            if book_index >= len(books):
                if book_index >= total_num_books:
                    break
                self.scroll_to_index(book_index)
                books = self.wait_for_books()
            print("Selecting from", len(books))
            print("Current index is", book_index)
            book = books[book_index]
            asin, title, authors = self.get_book_attributes(book)
            if title in BLOCKED:
                book_index += 1
                continue
            progress = self.get_progress(book)
            self.collected[asin] = {
                "title": title,
                "asin": asin,
                "progress": progress,
                "authors": authors
            }
            self.store_collected(book_index)
            book_index += 1

    def scroll_to_index(self, index: int) -> int:
        num_books = 0
        while True:
            books = self.wait_for_books()
            if index <= len(books) and index != -1:
                print("Scrolled to index")
                break
            if num_books == len(books):
                print("Scrolled to end")
                break
            num_books = len(books)
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(1.2)
        return num_books

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

    def store_collected(self, index: int) -> None:
        print("Storing", len(self.collected), "entries")
        with open(STORE_PATH, "w") as f:
            json.dump({
                "index": index,
                "collected": self.collected,
            }, f, indent=4)

    def restore_collected(self) -> int:
        if not os.path.exists(STORE_PATH):
            print("Nothing to restore")
            return 0
        with open(STORE_PATH) as f:
            collected = json.load(f)
        self.collected = collected.get("collected", {})
        print("Restored", len(self.collected), "books")
        index = collected.get("index", 0)
        print("Resumng from index", index)
        return index

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
