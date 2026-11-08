
from pathlib import Path
import time
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


URL = "https://localhost:2443/#/login"
USERNAME = "root"
PASSWORD = "0penBmc"
ATTEMPTS = 3

OVERVIEW_URL = "https://localhost:2443/#/"
POWER_URL = "https://localhost:2443/#/operations/server-power-operations"


def create_driver():
    driver_path = Path(__file__).parent / "drivers" / "yandexdriver.exe"

    options = webdriver.ChromeOptions()
    options.set_capability("acceptInsecureCerts", True)
    options.add_argument("--ignore-certificate-errors")

    service = Service(executable_path=str(driver_path))
    driver = webdriver.Chrome(service=service, options=options)

    return driver


def login(driver):
    wait = WebDriverWait(driver, 15)
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
    password_field.send_keys(PASSWORD)

    login_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space()='Log in']")
        )
    )
    login_button.click()

    wait.until(EC.title_is("Overview"))


def test_authentication():
    driver = create_driver()

    try:
        login(driver)
        assert driver.title == "Overview", "Авторизация не пройдена"
    finally:
        driver.quit()


def confirm_shutdown(driver):
    wait = WebDriverWait(driver, 10)

    confirm_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space()='Confirm']")
        )
    )

    confirm_button.click()


def check_status(driver, expected_status):
    print("Ждём 30 секунд...")
    time.sleep(30)

    driver.refresh()
    time.sleep(3)

    wait = WebDriverWait(driver, 15)

    if expected_status == "On":
        try:
            wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR,
                     '[data-test-id="serverPowerOperations-button-shutDown"]')
                )
            )
            print("Тест пройден: доступна кнопка Shut down.")
            return True

        except:
            print("Тест не пройден: кнопка Shut down не появилась.")
            return False

    elif expected_status == "Off":
        try:
            wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR,
                     '[data-test-id="serverPowerOperations-button-powerOn"]')
                )
            )
            print("Тест пройден: появилась кнопка Power on.")
            return True

        except:
            print("Тест не пройден: кнопка Power on не появилась.")
            return False

    return False


def power_on(driver):
    print("\nПроверка Power On")

    wait = WebDriverWait(driver, 15)

    button = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR,
             '[data-test-id="serverPowerOperations-button-powerOn"]')
        )
    )

    button.click()

    return check_status(driver, "On")


def power_off(driver):
    print("\nПроверка Power Off")

    wait = WebDriverWait(driver, 15)

    force_off = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR,
             '[data-test-id="serverPowerOperations-radio-shutdownImmediate"]')
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", force_off
    )
    force_off.click()

    button = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR,
             '[data-test-id="serverPowerOperations-button-shutDown"]')
        )
    )

    button.click()
    confirm_shutdown(driver)

    return check_status(driver, "Off")


def graceful_shutdown(driver):
    print("\nПроверка Graceful Shutdown")

    wait = WebDriverWait(driver, 15)

    radio = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR,
             '[data-test-id="serverPowerOperations-radio-shutdownOrderly"]')
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", radio
    )
    radio.click()

    shutdown_button = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR,
             '[data-test-id="serverPowerOperations-button-shutDown"]')
        )
    )

    shutdown_button.click()
    confirm_shutdown(driver)

    print("Операция подтверждена.")

    return check_status(driver, "Off")


def test_power():
    driver = create_driver()

    try:
        login(driver)
        driver.get(POWER_URL)

        time.sleep(3)

        power_on_buttons = driver.find_elements(
            By.CSS_SELECTOR,
            '[data-test-id="serverPowerOperations-button-powerOn"]'
        )

        power_off_buttons = driver.find_elements(
            By.CSS_SELECTOR,
            '[data-test-id="serverPowerOperations-button-powerOff"]'
        )

        reboot_buttons = driver.find_elements(
            By.CSS_SELECTOR,
            '[data-test-id="serverPowerOperations-button-reboot"]'
        )

        shutdown_buttons = driver.find_elements(
            By.CSS_SELECTOR,
            '[data-test-id="serverPowerOperations-button-shutDown"]'
        )

        if (len(power_on_buttons) > 0
                and power_on_buttons[0].is_displayed()):

            print("Начальное состояние: Power On")

            if power_on(driver):
                if power_off(driver):
                    if power_on(driver):
                        if graceful_shutdown(driver):
                            print("\nВсе проверки питания пройдены.")
                        else:
                            print("\nТест завершён: Graceful Shutdown не пройден.")
                    else:
                        print("\nТест завершён: Power On не пройден.")
                else:
                    print("\nТест завершён: Power Off не пройден.")
            else:
                print("\nТест завершён: проверка Power On не пройдена.")

        elif (len(power_off_buttons) > 0
                and power_off_buttons[0].is_displayed()):

            print("Начальное состояние: Power Off")

            if power_off(driver):
                if power_on(driver):
                    if graceful_shutdown(driver):
                        print("\nВсе проверки питания пройдены.")
                    else:
                        print("\nТест завершён: Graceful Shutdown не пройден.")
                else:
                    print("\nТест завершён: Power On не пройден.")
            else:
                print("\nТест завершён: Power Off не пройден.")

        elif (len(reboot_buttons) > 0
                and reboot_buttons[0].is_displayed()
                and len(shutdown_buttons) > 0
                and shutdown_buttons[0].is_displayed()):

            print("Начальное состояние: Reboot и Shut down")

            if graceful_shutdown(driver):
                if power_on(driver):
                    if power_off(driver):
                        print("\nВсе проверки питания пройдены.")
                    else:
                        print("\nТест завершён: Power Off не пройден.")
                else:
                    print("\nТест завершён: Power On не пройден.")
            else:
                print("\nТест завершён: Graceful Shutdown не пройден.")

        else:
            print("Тест не пройден: неизвестный вариант интерфейса.")

    finally:
        driver.quit()


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
            "Server manufacturer",
        ]

        missing_fields = []

        for field in fields:
            element = driver.find_element(
                By.XPATH,
                "//h3[normalize-space()='Server information']"
                "/ancestor::div[contains(@class, 'card-body')]"
                "//dt[normalize-space()='" + field + "']"
                "/following-sibling::dd[1]"
            )

            value = element.text.strip()

            if not value or value == "--":
                missing_fields.append(field)

        assert not missing_fields, (
            "Отсутствует информация о сервере: "
            + ", ".join(missing_fields)
        )

    finally:
        driver.quit()


def test_account_lockout():
    driver = create_driver()
    wait = WebDriverWait(driver, 10)

    def login_with_password(password):
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
        login_button.click()

    try:
        for _ in range(ATTEMPTS):
            login_with_password("wrong_password")
            time.sleep(1)

        login_with_password(PASSWORD)

        try:
            WebDriverWait(driver, 5).until(
                EC.title_is("Overview")
            )
        except TimeoutException:
            pass
        else:
            pytest.fail(
                "Блокировка не работает: вход разрешён "
                "после трёх неправильных попыток."
            )

    finally:
        driver.quit()