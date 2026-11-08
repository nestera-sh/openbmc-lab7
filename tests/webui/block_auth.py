
from pathlib import Path
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


driver_path = Path(__file__).parent / "drivers" / "yandexdriver.exe"

options = webdriver.ChromeOptions()
options.set_capability("acceptInsecureCerts", True)
options.add_argument("--ignore-certificate-errors")

service = Service(executable_path=str(driver_path))
driver = webdriver.Chrome(service=service, options=options)

URL = "https://localhost:2443/#/login"
USERNAME = "root"
PASSWORD = "0penBmc"
ATTEMPTS = 3

wait = WebDriverWait(driver, 10)



def login(password):
    driver.get(URL)

    username_field = wait.until(
        EC.visibility_of_element_located((By.ID, "username"))
    )
    username_field.clear()
    username_field.send_keys(USERNAME)

    password_field = wait.until(
        EC.visibility_of_element_located((By.ID, "password"))
    )
    password_field.clear()
    password_field.send_keys(password)

    login_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space()='Log in']")
        )
    )

    time.sleep(1)
    login_button.click()


try:
    print("Начинаем проверку блокировки учётной записи.")

    for attempt in range(ATTEMPTS):
        login("wrong_password")
        print(f"Выполнена неудачная попытка №{attempt + 1}")
        time.sleep(1)

    print("Проверяем вход с правильным паролем...")
    login(PASSWORD)

    try:
        WebDriverWait(driver, 5).until(
            EC.title_is("Overview")
        )
        print("ТЕСТ НЕ ПРОЙДЕН: вход с правильным паролем разрешён.")

    except TimeoutException:
        print("Вход не выполнен.")
        print("Проверь счётчик PAM для подтверждения блокировки.")

    input("Браузер оставлен открытым. Нажми Enter для завершения...")

finally:
    driver.quit()
