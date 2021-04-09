""" The bccr package setup.
Based on setuptools

Randall Romero-Aguilar, 2015-2020
"""

from setuptools import setup
from codecs import open
#from os import path

#here = path.abspath(path.dirname(__file__))

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='bccr',
    version='2021.03',
    description='Herramientas para descargar datos del Banco Central de Costa Rica',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Randall Romero-Aguilar',
    author_email='randall.romero@outlook.com',
    url='http://randall-romero.com/code/bccr',
    license='MIT',
    keywords='BCCR datos',
    packages=['bccr', 'demos', ],
    python_requires='>=3.7',
    install_requires=['pandas', 'numpy', 'anytree',  'requests', 'beautifulsoup4'],
    package_data={'bccr': ['data/indicadores.pkl', 'data/indicators.pkl', 'data/cuadros.pkl']},
    include_package_data=True
)



