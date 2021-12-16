from django import template
from django.urls import reverse

register = template.Library()

@register.simple_tag
def url_if(pathname):
    try:
        print(pathname)
        print( reverse(pathname))
        return reverse(pathname)
    except:
        return None

