from django import forms


LOCAL_DATE_FORMAT = "%d.%m.%Y"
LOCAL_DATE_INPUT_FORMATS = ["%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"]
LOCAL_DATE_WIDGET_ATTRS = {"class": "form-control js-date"}


def localized_date_field(**kwargs):
    attrs = kwargs.pop("attrs", None)
    widget_attrs = LOCAL_DATE_WIDGET_ATTRS.copy()
    if attrs:
        widget_attrs.update(attrs)

    kwargs.setdefault(
        "widget",
        forms.DateInput(format=LOCAL_DATE_FORMAT, attrs=widget_attrs),
    )
    kwargs.setdefault("input_formats", list(LOCAL_DATE_INPUT_FORMATS))
    return forms.DateField(**kwargs)
