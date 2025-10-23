from datetime import datetime

from buildbot.plugins import util


@util.renderer
def current_year(props):
    """Render the current year as a string."""
    return datetime.now().strftime("%y")


@util.renderer
def current_month(props):
    """Render the current month as a string."""
    return datetime.now().strftime("%m")


@util.renderer
def current_day(props):
    """Render the current day as a string."""
    return datetime.now().strftime("%d")
