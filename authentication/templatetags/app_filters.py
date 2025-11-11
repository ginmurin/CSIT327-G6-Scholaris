from django import template

register = template.Library()


@register.filter
def format_app_time(minutes):
    """
    Convert total minutes to a human-readable format like '2h 30m'
    """
    if not minutes:
        return "0m"
    
    total_minutes = int(minutes)
    hours = total_minutes // 60
    mins = total_minutes % 60
    
    if hours == 0:
        return f"{mins}m"
    elif mins == 0:
        return f"{hours}h"
    else:
        return f"{hours}h {mins}m"
