from pathlib import Path
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://localhost:2443/#/login"
USERNAME = "root"
PASSWORD = "0penBmc"

def create_driver():
    options = webdriver.ChromeOptions()
    options.set_capability("acceptInsecureCerts", True)
    options.add_argument("--ignore-certificate-errors")
    

    if os.name != 'nt': 
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox") 
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        

        service = Service("/usr/bin/chromedriver")
    else:  # Если это Windows (твой локальный компьютер)

        driver_path = Path(__file__).parent / "drivers" / "yandexdriver.exe"
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