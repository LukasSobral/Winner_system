from django import template
import calendar
import datetime

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def to(start, end):
    return range(start, end+1)

@register.filter
def get_month_name(month_number):
    return calendar.month_name[int(month_number)].capitalize()

@register.filter
def add_days(date_value, days):
    return date_value + datetime.timedelta(days=int(days))

@register.filter(name='add_class')
def add_class(field, css_class):
    try:
        return field.as_widget(attrs={"class": css_class})
    except AttributeError:
        return field 

@register.filter
def dict_get(dictionary, key):
    return dictionary.get(key)

@register.filter
def as_p(form):
    return form.as_p()