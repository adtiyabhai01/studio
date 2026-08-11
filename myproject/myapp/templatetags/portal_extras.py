from django import template

register = template.Library()

STATUS_CLASSES = {
    "NEW": "is-new",
    "CONTACTED": "is-contact",
    "FOLLOW_UP": "is-followup",
    "BOOKED": "is-booked",
    "COMPLETED": "is-completed",
    "CLOSED": "is-closed",
}


@register.filter
def dict_get(value, key):
    """Usage: {{ budget_map|dict_get:enquiry.budget }} -> dict value or ''."""
    try:
        return value.get(key, "")
    except AttributeError:
        return ""


@register.filter
def attr(value, name):
    """Usage: {{ theme|attr:"primary" }} -> attribute value or ''."""
    try:
        return getattr(value, name, "")
    except Exception:
        return ""


@register.simple_tag
def status_class(status):
    """Map an enquiry status value to a CSS class for the dropdown/row."""
    return STATUS_CLASSES.get(status, "is-closed")