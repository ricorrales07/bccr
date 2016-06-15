from distutils.core import setup


setup(
    name='bccr',
    version='0.1',
    description='Tools for downloading data from the Central Bank of Costa Rica',
    author='Randall Romero-Aguilar',
    author_email='randall.romero@outlook.com',
    url='randall-romero.com/code',
    download_url='www.randall-romero.com/code',
    packages=['bccr', 'demos', ],
    requires=['nose', 'numpy', 'pandas(>=0.18)', 'matplotlib', 'seaborn'],
    package_data={'bccr': ['bccr/data/*.pkl']},
    include_package_data=True
)

