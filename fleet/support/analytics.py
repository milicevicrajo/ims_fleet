from collections import defaultdict


def net_maintenance_cost(service_cost, requisition_cost=0, insurance_recovery=0):
    return (service_cost or 0) + (requisition_cost or 0) - (insurance_recovery or 0)


def is_red_zone(long_term_rental, value, net_cost):
    return not long_term_rental and (value or 0) > 0 and (net_cost or 0) > (value or 0)


def percentile(values, percent):
    values = sorted(values)
    if not values:
        return 0
    if len(values) == 1:
        return values[0]
    position = (len(values) - 1) * percent / 100
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    fraction = position - lower
    return values[lower] + (values[upper] - values[lower]) * fraction


def cost_per_km_thresholds(rows):
    grouped = defaultdict(list)
    for row in rows:
        if row["cost_per_km"] is not None:
            grouped[row["category"]].append(row["cost_per_km"])

    thresholds = {}
    for category, values in grouped.items():
        thresholds[category] = {
            "category": category,
            "vehicle_count": len(values),
            "median": percentile(values, 50),
            "p75": percentile(values, 75),
            "p90": percentile(values, 90),
            "average": sum(values) / len(values) if values else 0,
        }
    return thresholds


def cost_per_km_status(value, threshold):
    if value is None:
        return "Opomena"
    if not threshold:
        return "Nema praga"
    if value <= threshold["median"]:
        return "Dobro"
    if value <= threshold["p75"]:
        return "Za pracenje"
    if value <= threshold["p90"]:
        return "Rizicno"
    return "Neisplativo"
