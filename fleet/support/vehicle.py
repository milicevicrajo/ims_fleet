import re


def format_license_plate(plate):
    plate = plate.replace("â€“", "-").replace("-", "").replace(" ", "").upper()
    plate = re.sub(r"[^A-Za-z0-9]", "", plate)

    match = re.match(r"^([A-Z]{2})(\d{3,4})([A-Z]{2})$", plate)
    if match:
        return f"{match.group(1)}{match.group(2)}-{match.group(3)}"

    return plate
