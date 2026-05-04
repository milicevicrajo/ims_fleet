from collections import defaultdict


def net_maintenance_cost(service_cost, requisition_cost=0, insurance_recovery=0):
    return (service_cost or 0) + (requisition_cost or 0) - (insurance_recovery or 0)


def is_red_zone(long_term_rental, value, net_cost):
    return not long_term_rental and (value or 0) > 0 and (net_cost or 0) > (value or 0)


# Fiksni pragovi troška po km prema maksimalnoj dozvoljenoj masi vozila (RSD/km)
# (max_masa_kg, oznaka, dobro, za_pracenje, rizicno)  — iznad "rizicno" = Neisplativo
_WEIGHT_CLASS_THRESHOLDS = [
    (3500,        'Putnička vozila (do 3.5t)',        25,  40,  60),
    (7500,        'Laka teretna (3.5t – 7.5t)',       45,  70, 100),
    (12000,       'Srednja teretna (7.5t – 12t)',     70, 110, 140),
    (float('inf'), 'Teška teretna (preko 12t)',      120, 150, 175),
]


def fixed_cost_per_km_ranges():
    """Fiksni opsezi granica po klasi mase, nezavisno od perioda analize."""
    ranges = []
    prev_max = 0
    for max_w, label, ok, watch, risky in _WEIGHT_CLASS_THRESHOLDS:
        ranges.append({
            'weight_class_label': label,
            'from_weight_kg': prev_max,
            'to_weight_kg': None if max_w == float('inf') else max_w,
            'ok': ok,
            'watch': watch,
            'risky': risky,
        })
        prev_max = max_w
    return ranges


def fixed_cost_per_km_threshold(max_weight_kg):
    """Vraća fiksne pragove (ok/watch/risky) za datu max dozvoljenu masu vozila."""
    weight = float(max_weight_kg or 0)
    for max_w, label, ok, watch, risky in _WEIGHT_CLASS_THRESHOLDS:
        if weight <= max_w:
            return {'weight_class_label': label, 'ok': ok, 'watch': watch, 'risky': risky}
    return {'weight_class_label': 'Nepoznato', 'ok': 60, 'watch': 100, 'risky': 150}


def cost_per_km_thresholds(rows):
    """Grupna statistika po klasama mase sa fiksnim pragovima za prikaz u tabeli."""
    grouped = defaultdict(lambda: {'values': [], 'threshold': None, 'weight_class_label': ''})
    for row in rows:
        if row["cost_per_km"] is not None:
            t = fixed_cost_per_km_threshold(row.get("maximum_permissible_weight", 0))
            key = t['weight_class_label']
            grouped[key]['values'].append(row["cost_per_km"])
            grouped[key]['threshold'] = t
            grouped[key]['weight_class_label'] = key

    thresholds = {}
    for key, data in grouped.items():
        values = data['values']
        t = data['threshold']
        thresholds[key] = {
            "category": key,
            "weight_class_label": key,
            "vehicle_count": len(values),
            "average": sum(values) / len(values) if values else 0,
            "ok": t['ok'],
            "watch": t['watch'],
            "risky": t['risky'],
        }
    return thresholds


def cost_per_km_status(value, threshold):
    if value is None:
        return "Opomena"
    if not threshold:
        return "Nema praga"
    if value <= threshold["ok"]:
        return "Dobro"
    if value <= threshold["watch"]:
        return "Za praćenje"
    if value <= threshold["risky"]:
        return "Rizično"
    return "Neisplativo"
