from django import template

register = template.Library()


@register.filter(name='time_to_str')
def time_to_str(time):
    return time.__str__()[:5]
