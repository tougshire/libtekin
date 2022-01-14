from django import template
from django.urls import reverse
from django.conf import settings

register = template.Library()

@register.simple_tag
def global_menu_template():
    try:
        return settings.GLOBAL_MENU_TEMPLATE
    except:
        return None

@register.simple_tag
def global_css_file():
    try:
        return settings.GLOBAL_CSS_FILE
    except:
        return None


