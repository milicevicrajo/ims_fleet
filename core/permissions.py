from django.urls import URLPattern, URLResolver


def collect_url_pattern_names(patterns, prefix=None):
    names = set()
    _collect_url_pattern_names(patterns, names)
    if prefix:
        return sorted(f"{prefix}:{name}" for name in names)
    return sorted(names)


def _collect_url_pattern_names(patterns, acc):
    for pattern in patterns:
        if isinstance(pattern, URLPattern):
            if pattern.name:
                acc.add(pattern.name)
        elif isinstance(pattern, URLResolver):
            _collect_url_pattern_names(pattern.url_patterns, acc)
    return acc
