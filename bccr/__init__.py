"""bccr: A Python library to import data from the Central Bank of Costa Rica

"""

from .download import api, downloadChart
from .fetch import parse, read
from .scrape import search, findAllCharts, updateIndicators, loadIndicators
