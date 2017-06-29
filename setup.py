"""Crawl EDGAR database to download index files and filings.

Contains the edgar class.

Sample script:
my_edgar = edgar()
my_edgar.definesearch("20150101", "20151231", filter_formtype=["8-K"])
my_edgar.getindex()
my_edgar.getfilings(text_only=False, sample_size=10,
                    fname_form="%Y/%m/%Y%m_%company")
my_edgar.cur_filings

"""
from setuptools import setup


def readme():
    """Read readme.rst file and return as string."""
    with open('README.rst') as f:
        return f.read()


setup(name='edgarsearch',
      version='0.1',
      description='Crawl EDGAR database to download index files and filings.',
      long_description=readme(),
      keywords='EDGAR index filings 8-K 10-K',
      url='https://github.com/markdembo/edgarsearch',
      author='Mark Dembo',
      author_email='mark.dembo@student.unisg.ch',
      license='MIT',
      packages=['edgarsearch'],
      install_requires=[
          'pandas',
      ],
      zip_safe=False)
