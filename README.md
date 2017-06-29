# Edgarsearch
> Crawl EDGAR database to download index files and filings.

Use this crawler to download index files and filings from the SEC EGDAR Database based on multiple criteria (time period, form type and CIK). The crawler is capable of restoring the original files (html, jpg, pdf, ...) from the filing and saving these using your preferred file name pattern.

## Getting started
### Install

Simply install egdarsearch using pip:

```shell
pip install edgarsearch
```

This code will install the edgarsearch package and its dependencies (Pandas).


### Import

Import the package using

```shell
import edgarsearch
```

## Features

This project makes it easy to:
* Search the EDGAR database
* Download index files based on your searches
* Download filings based in your searches using multithreading to speed up the process
* Keep the filings either in raw format as obtained from the server or as orgininal documents (html, jpg, pdf)
* Use your own pattern for file names to suit your need

## Contributing

If you'd like to contribute, please fork the repository and make changes as
you'd like. Pull requests are warmly welcome.

## Licensing

This project is licensed under the MIT License
