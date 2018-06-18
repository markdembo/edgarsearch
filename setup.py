from setuptools import setup

setup(name="edgarsearch",
      version="0.3",
      description="Crawl EDGAR database to download index files and filings.",
      keywords="EDGAR index filings 8-K 10-K",
      url="https://github.com/markdembo/edgarsearch",
      download_url="https://github.com/markdembo/edgarsearch/archive/0.2.tar.gz",
      author="Mark Dembo",
      author_email="mark.dembo@student.unisg.ch",
      license="MIT",
      packages=["edgarsearch"],
      install_requires=[
          "pandas",
          "tqdm"
      ],
      )
