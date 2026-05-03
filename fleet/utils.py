import os
import re
from decimal import Decimal, ROUND_HALF_UP

from .support.fuel import (
    calculate_average_fuel_consumption,
    calculate_average_fuel_consumption_ever,
    date_range_for_datetime_field,
    filter_nis_fuel_queryset,
    filter_omv_fuel_queryset,
    get_fuel_consumption_queryset,
)
from .support.vehicle import format_license_plate


def get_latest_download_file(download_path):
    files = os.listdir(download_path)
    paths = [os.path.join(download_path, basename) for basename in files]
    return max(paths, key=os.path.getctime)


def normalize_decimal(value):
    try:
        return Decimal(str(value).strip()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception:
        return None


def sanitize_filename(filename):
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", filename)
