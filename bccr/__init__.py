"""bccr: A Python library to import data from the Central Bank of Costa Rica

"""

from .download import api, downloadChart, web
from .fetch import parse, read
from .scrape import search, findAllCharts, updateIndicators, loadIndicators
from .utils import columns_rename
from .gee import ServicioWeb