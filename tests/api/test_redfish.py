import json
import logging
import subprocess
import time
from urllib.parse import urljoin

import pytest
import requests
import urllib3


BASE_URL = "https://localhost:2443"
USERNAME = "root"
PASSWORD = "0penBmc"

SESSIONS_URL = BASE_URL + "/redfish/v1/SessionService/Sessions"
SYSTEM_URL = BASE_URL + "/redfish/v1/Systems/system"

SENSORS_URL = BASE_URL + "/redfish/v1/Chassis/chassis/Sensors"
THERMAL_METRICS_URL = (
    BASE_URL
    + "/redfish/v1/Chassis/chassis/ThermalSubsystem/ThermalMetrics"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def show_response(name, response):
    print("\n========== {} ==========".format(name))
    print("HTTP status:", response.status_code)

    try:
        data = response.json()
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except ValueError:
        if response.text:
            print(response.text)
        else:
            print("<пустое тело ответа>")


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def normalize_sensor_name(name):

    name = str(name).lower()
    name = name.replace("processor", "cpu")
    name = name.replace("temperature", "temp")

    return "".join(
        char for char in name
        if char.isalnum()
    )


@pytest.fixture
def api_session():
    session = requests.Session()
    session.auth = (USERNAME, PASSWORD)
    session.verify = False

    yield session

    session.close()


def test_authentication(api_session):
    response = api_session.post(
        SESSIONS_URL,
        json={
            "UserName": USERNAME,
            "Password": PASSWORD
        },
        timeout=10
    )

    show_response("Создание Redfish-сессии", response)

    token = response.headers.get("X-Auth-Token")
    location = response.headers.get("Location")

    logger.info("Код ответа авторизации: %s", response.status_code)

    try:
        # OpenBMC может вернуть 200 или 201 при создании сессии.
        assert response.status_code in (200, 201), (
            "Ошибка авторизации: HTTP "
            + str(response.status_code)
        )

        assert token, "В ответе отсутствует X-Auth-Token"

    finally:

        if token and location:
            location = urljoin(BASE_URL + "/", location)

            try:
                close_response = api_session.delete(
                    location,
                    headers={"X-Auth-Token": token},
                    timeout=10
                )

                show_response("Закрытие Redfish-сессии", close_response)

            except requests.RequestException as error:
                logger.warning(
                    "Не удалось закрыть Redfish-сессию: %s",
                    error
                )


def test_system_info(api_session):
    response = api_session.get(
        SYSTEM_URL,
        timeout=10
    )

    show_response("Информация о системе", response)

    assert response.status_code == 200, (
        "Не удалось получить информацию о системе"
    )

    data = response.json()

    assert "Status" in data, (
        "В ответе отсутствует поле Status"
    )

    assert "PowerState" in data, (
        "В ответе отсутствует поле PowerState"
    )

    logger.info("Состояние питания: %s", data["PowerState"])
    logger.info("Статус системы: %s", data["Status"])

def wait_for_power_state(api_session, expected_state):
    for attempt in range(5):
        try:
            response = api_session.get(SYSTEM_URL, timeout=3)

            if response.status_code == 404:
                show_response("Ошибка: ресурс системы не найден", response)
                return False

            if response.status_code != 200:
                show_response("Ошибка получения состояния системы", response)
                return False

            data = response.json()
            power_state = data.get("PowerState")

            logger.info(
                "Попытка %d/5: PowerState = %s",
                attempt + 1,
                power_state
            )

            if power_state == expected_state:
                show_response("Состояние системы", response)
                return True

        except (requests.Timeout, requests.ConnectionError) as error:
            logger.warning("Ошибка запроса к Redfish: %s", error)

        time.sleep(1)

    return False


def test_power_on(api_session):
    response = api_session.post(
        SYSTEM_URL + "/Actions/ComputerSystem.Reset",
        json={"ResetType": "On"},
        timeout=10
    )

    show_response("Команда включения сервера", response)

    # В нашей эмуляции ранее возвращался HTTP 204.
    assert response.status_code in (200, 202, 204), (
        "Не удалось отправить команду включения: HTTP "
        + str(response.status_code)
    )

    assert wait_for_power_state(api_session, "On"), (
        "Redfish не сообщил состояние On"
    )


def test_power_off(api_session):
    response = api_session.post(
        SYSTEM_URL + "/Actions/ComputerSystem.Reset",
        json={"ResetType": "ForceOff"},
        timeout=10
    )

    show_response("Команда выключения сервера", response)

    assert response.status_code in (200, 202, 204), (
        "Не удалось отправить команду выключения: HTTP "
        + str(response.status_code)
    )

    assert wait_for_power_state(api_session, "Off"), (
        "Redfish не сообщил состояние Off"
    )


def test_cpu_temperature(api_session):
    response = api_session.get(
        THERMAL_METRICS_URL,
        timeout=10
    )

    show_response("Температурные показатели Redfish", response)

    assert response.status_code == 200, (
        "Не удалось получить ThermalMetrics"
    )

    data = response.json()
    readings = data.get("TemperatureReadingsCelsius", [])

    logger.info(
        "Всего температурных показаний: %d",
        len(readings)
    )

    assert readings, (
        "В ThermalMetrics отсутствуют температурные показания"
    )

    cpu_count = 0

    for item in readings:
        sensor_data = {}
        source_uri = item.get("DataSourceUri")


        if source_uri:
            sensor_url = urljoin(BASE_URL + "/", source_uri)

            sensor_response = api_session.get(
                sensor_url,
                timeout=10
            )

            show_response(
                "Датчик " + source_uri,
                sensor_response
            )

            if sensor_response.status_code == 200:
                sensor_data = sensor_response.json()

        description = " ".join(
            str(value)
            for value in [
                item.get("Name", ""),
                item.get("DeviceName", ""),
                item.get("PhysicalContext", ""),
                item.get("DataSourceUri", ""),
                sensor_data.get("Name", ""),
                sensor_data.get("PhysicalContext", "")
            ]
        ).lower()

        if "cpu" not in description and "processor" not in description:
            continue

        reading = item.get("Reading")

        if not is_number(reading):
            reading = item.get("ReadingCelsius")

        if not is_number(reading):
            reading = sensor_data.get("Reading")

        if not is_number(reading):
            reading = sensor_data.get("ReadingCelsius")

        assert is_number(reading), (
            "Для датчика CPU отсутствует числовое показание: "
            + description
        )

        lower = sensor_data.get("LowerThresholdCritical")
        upper = sensor_data.get("UpperThresholdCritical")

        if not is_number(lower):
            lower = item.get("LowerThresholdCritical")

        if not is_number(upper):
            upper = item.get("UpperThresholdCritical")

        assert is_number(lower) or is_number(upper), (
            "Для датчика CPU Redfish не предоставил "
            "критические пороги температуры: "
            + description
        )

        if is_number(lower):
            assert reading >= lower, (
                "Температура CPU ниже критического порога: "
                + str(reading)
            )

        if is_number(upper):
            assert reading <= upper, (
                "Температура CPU выше критического порога: "
                + str(reading)
            )

        cpu_count += 1

        logger.info(
            "Температура CPU: %s; нижний порог: %s; верхний порог: %s",
            reading,
            lower,
            upper
        )

    assert cpu_count > 0, (
        "Redfish не предоставил проверяемых показаний температуры CPU"
    )


def test_cpu_sensors_redfish_ipmi(api_session):
    # Сначала получаем список датчиков Redfish.
    response = api_session.get(
        SENSORS_URL,
        timeout=10
    )

    show_response("Коллекция датчиков Redfish", response)

    assert response.status_code == 200, (
        "Не удалось получить датчики Redfish"
    )

    members = response.json().get("Members", [])

    redfish_names = {}
    redfish_values = {}

    for member in members:
        uri = member.get("@odata.id")

        if not uri:
            continue

        sensor_response = api_session.get(
            urljoin(BASE_URL + "/", uri),
            timeout=10
        )

        show_response("Датчик Redfish " + uri, sensor_response)

        if sensor_response.status_code != 200:
            continue

        sensor = sensor_response.json()

        name = str(
            sensor.get("Name")
            or sensor.get("Id")
            or uri
        )

        description = " ".join(
            [
                name,
                str(sensor.get("PhysicalContext", "")),
                uri
            ]
        ).lower()

        if "cpu" not in description and "processor" not in description:
            continue

        key = normalize_sensor_name(name)
        redfish_names[key] = name

        value = sensor.get("Reading")

        if not is_number(value):
            value = sensor.get("ReadingCelsius")

        if is_number(value):
            redfish_values[key] = float(value)


    try:
        result = subprocess.run(
            [
                "ipmitool",
                "-I", "lanplus",
                "-H", "127.0.0.1",
                "-p", "2623",
                "-U", USERNAME,
                "-P", PASSWORD,
                "sensor", "list"
            ],
            capture_output=True,
            text=True,
            timeout=15
        )

    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        pytest.fail(
            "Не удалось выполнить ipmitool: " + str(error)
        )

    print("\n========== Датчики CPU из IPMI ==========")

    if result.stderr:
        print(result.stderr)

    assert result.returncode == 0, (
        "Ошибка получения датчиков IPMI: " + result.stderr
    )

    ipmi_names = {}
    ipmi_values = {}

    for line in result.stdout.splitlines():
        parts = [part.strip() for part in line.split("|")]

        if len(parts) < 2:
            continue

        name = parts[0]
        description = name.lower()

        if "cpu" not in description and "processor" not in description:
            continue

        print(line)

        key = normalize_sensor_name(name)
        ipmi_names[key] = name

        try:
            value = float(parts[1])
        except ValueError:
            continue

        ipmi_values[key] = value

    logger.info("Датчики CPU Redfish: %s", redfish_names)
    logger.info("Датчики CPU IPMI: %s", ipmi_names)
    logger.info("Числовые показания Redfish: %s", redfish_values)
    logger.info("Числовые показания IPMI: %s", ipmi_values)

    assert redfish_names, (
        "Redfish не вернул датчики CPU"
    )

    assert ipmi_names, (
        "IPMI не вернул датчики CPU"
    )

    common_names = set(redfish_names) & set(ipmi_names)

    assert common_names, (
        "Не найдено совпадающих имён датчиков CPU в Redfish и IPMI"
    )

    common_values = (
        common_names
        & set(redfish_values)
        & set(ipmi_values)
    )

    assert common_values, (
        "Имена датчиков совпадают, но нет числовых показаний "
        "для сравнения Redfish и IPMI"
    )

    for name in common_values:
        redfish_value = redfish_values[name]
        ipmi_value = ipmi_values[name]

        assert abs(redfish_value - ipmi_value) <= 1.0, (
            "Значения датчика {} отличаются: Redfish={}, IPMI={}"
            .format(
                name,
                redfish_value,
                ipmi_value
            )
        )