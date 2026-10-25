"""Pengaturan bersama untuk semua tes."""
import copy
import os
import sys
from datetime import datetime, timedelta

import pytest

# Agar `import app` dan `import services` berfungsi dari folder tests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def buat_data_contoh():
    """Data tiruan berbentuk seperti respons Open-Meteo (tanpa internet)."""
    awal = datetime(2026, 10, 25, 0, 0)
    jam = [(awal + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M") for i in range(7 * 24)]
    hari = [(awal + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    return {
        "timezone": "Asia/Pontianak",
        "timezone_abbreviation": "WIB",
        "current": {"time": "2026-10-25T14:15", "interval": 900, "temperature_2m": 33.1,
                    "relative_humidity_2m": 62, "precipitation": 0.0, "weather_code": 1, "wind_speed_10m": 12.4},
        "hourly": {"time": jam,
                   "temperature_2m": [25.0 + (i % 24) / 3 for i in range(len(jam))],
                   "precipitation_probability": [(i * 5) % 100 for i in range(len(jam))],
                   "precipitation": [0.0] * len(jam)},
        "daily": {"time": hari, "weather_code": [1, 2, 61, 63, 65, 3, 0],
                  "temperature_2m_max": [34, 34, 33, 32, 31, 33, 34],
                  "temperature_2m_min": [25, 25, 24, 24, 24, 24, 25],
                  "precipitation_probability_max": [10, 20, 40, 60, 70, 30, 20],
                  "precipitation_sum": [0.0, 0.2, 3.0, 8.5, 20.1, 1.0, 0.0]},
    }


@pytest.fixture
def data_contoh():
    return copy.deepcopy(buat_data_contoh())