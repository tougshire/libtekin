from django import template
from django.urls import reverse

register = template.Library()

@register.simple_tag
def url_if(pathname):
    try:
        return reverse(pathname)
    except:
        return None

