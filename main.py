import time
import logging
from typing import Dict, Optional, Union
from enviroplus import gas  # type: ignore
from bme280 import BME280  # type: ignore
from pms5003 import PMS5003, ChecksumMismatchError, ReadTimeoutError as pmsReadTimeoutError  # type: ignore
from smbus import SMBus  # type: ignore
from ltr559 import LTR559 
from datetime import datetime
import psycopg2
import RPi.GPIO as GPIO
import os

#  PostgreSQL connection
conn = psycopg2.connect(
    host=os.environ.get("DATABASE_HOST"),
    port=os.environ.get("DATABASE_PORT"),
    database=os.environ.get("DATABASE_DB"),
    user=os.environ.get("DATABASE_USER"),
    password=os.environ.get("DATABASE_PASSWORD")
)

cursor = conn.cursor()

def read_data(bme280: BME280, pms5003: PMS5003, lux_sensor: LTR559) -> Dict[str, Union[int, float]]:
    values = {}
    values["temperature"] = int(bme280.get_temperature())
    values["pressure"] = int(bme280.get_pressure())
    values["humidity"] = int(bme280.get_humidity())

    gas_data = gas.read_all()
    values["oxidised"] = int(gas_data.oxidising)
    values["reduced"] = int(gas_data.reducing)
    values["nh3"] = int(gas_data.nh3)
    
    values["motion"] = bool(GPIO.input(4))
    try:
        pms_data = pms5003.read()
        values["pm1"] = pms_data.pm_ug_per_m3(1.0)
        values["pm2_5"] = pms_data.pm_ug_per_m3(2.5)
        values["pm10"] = pms_data.pm_ug_per_m3(10)
        values["lux"] = int(lux_sensor.get_lux())
    except Exception:
        logging.exception("read failed")
        values["pm1"] = None
        values["pm2_5"] = None
        values["pm10"] = None
        values["lux"] = None

    return values

def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(4, GPIO.IN)

    bus = SMBus(1)
    bme280 = BME280(i2c_dev=bus)
    pms5003 = PMS5003()
    lux_sensor = LTR559()
    
    while True:
        data = read_data(bme280, pms5003, lux_sensor)

        try:
            cursor.execute("""
                INSERT INTO data (
                    timestamp, temperature, pressure, humidity,
                    oxidised, reduced, nh3,
                    pm1, pm2_5, pm10, motion, lux
                ) VALUES (
                    NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                data["temperature"],
                data["pressure"],
                data["humidity"],
                data["oxidised"],
                data["reduced"],
                data["nh3"],
                data["pm1"],
                data["pm2_5"],
                data["pm10"],
                data["motion"],
                data["lux"]
            ))

            conn.commit()
            print(f" Saved data: {data}")

        except Exception as e:
            print(f"error while writing to db: {e}")
            conn.rollback()

        time.sleep(10)

if __name__ == "__main__":
    main()if __name__ == "__main__":

