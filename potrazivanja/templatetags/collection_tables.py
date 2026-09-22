from django import template

register = template.Library()


@register.simple_tag
def collection_columns(columns, kind, partner=None, presentation=None):
    """Keep source indexes stable while arranging columns for display."""
    indexes = list(range(len(columns)))
    if presentation != 'pretty':
        if kind in ('partners', 'jobs', 'review'):
            indexes = [1, 0, *range(3, len(columns)), 2]
        elif kind == 'directory':
            indexes = [1, 0, 2, 3]
        elif kind in ('reminders', 'letters', 'claims'):
            indexes = [0, 3, 4, 2, 5, 6, 7, 8, 9, 10]
        elif kind in ('calls', 'notes'):
            indexes.remove(1)  # The selected page already identifies the record type.
    result = []
    for index in indexes:
        title = columns[index]
        if partner and title in ('Partner', 'Šifra partnera', 'Naziv'):
            continue
        result.append({'index': index, 'title': title})
    return result
