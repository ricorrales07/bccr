try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
   
config = {
    'description': 'bccr: A Toolbox to download and prepare data from the Central Bank of Costa Rica',
    'author': 'Randall Romero-Aguilar',
    'url': 'URL to get it at.',
    'donwload_url': 'Where do download it.',
    'author_email': 'randall.romero@outlook.com',
    'version':'0.1',
    'install_requires':['nose'],
    'packages': ['bccr'],
    'scripts':[],
    'name': 'projectname'
    }
    
setup(**config)
setup(requires=['nose', 'numpy', 'pandas', 'matplotlib', 'seaborn'], **config)