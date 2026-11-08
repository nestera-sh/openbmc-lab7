
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from main import create_driver, login
import time


OVERVIEW_URL = "https://localhost:2443/#/"


def test_server_info():
    driver = create_driver()
    wait = WebDriverWait(driver, 15)

    try:
        login(driver)
        driver.get(OVERVIEW_URL)

        wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//h3[normalize-space()='Server information']")
            )
        )

        fields = [
            "Model",
            "Serial number",
            "Server manufacturer"
        ]

        all_data_exists = True

        print("Проверка информации о сервере\n\n")
        time.sleep(15)
        for field in fields:
            element = driver.find_element(
                By.XPATH,
                "//h3[normalize-space()='Server information']"
                "/ancestor::div[contains(@class, 'card-body')]"
                "//dt[normalize-space()='" + field + "']"
                "/following-sibling::dd[1]"
            )

            value = element.text.strip()
            print(field + ": " + value)

            if value == "" or value == "--":
                all_data_exists = False

        if all_data_exists:
            print("Тест пройден.\n\n")
        else:
            print("Тест не пройден: часть информации отсутствует.\n\n")

        time.sleep(15)

    finally:
        driver.quit()


test_server_info()
