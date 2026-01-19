from django import template

register = template.Library()


@register.filter
def currency(value):
    """Format a number as currency with £ sign and commas"""
    try:
        value = float(value)
        return "£{:,.0f}".format(value)
    except (ValueError, TypeError):
        return "£0"
