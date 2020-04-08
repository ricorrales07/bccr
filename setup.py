""" The bccr package setup.
Based on setuptools

Randall Romero-Aguilar, 2015-2020
"""

from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here,'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='bccr',
    version='2020.04.08',
    description='Herramientas para descargar datos del Banco Central de Costa Rica',
    long_description_content_type='text/markdown',
	long_description=long_description,
    author='Randall Romero-Aguilar',
    author_email='randall.romero@outlook.com',
    url='http://randall-romero.com/code/bccr',
    classifiers=['Development Status :: 4 - Beta',
                 'Intended Audience :: Economists',
                 'Topic :: Data processing',
                 'License :: OSI Approved :: MIT License',
                 'Programming Language :: Python :: 3.7'],
    keywords='BCCR datos',
    download_url='http://randall-romero.com/code',
    packages=['bccr', 'demos', ],
    python_requires='>=3.7',
    install_requires=['pandas', 'numpy', 'anytree',  'requests', 'beautifulsoup4'],
    package_data={'bccr': ['data/indicadores.pkl', 'data/indicators.pkl', 'data/cuadros.pkl']},
    include_package_data=True
)



