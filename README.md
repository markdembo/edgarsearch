# Edgarsearch
> Crawl EDGAR database to download index files and filings.

Use this crawler to download index files and filings from the SEC EGDAR Database based on multiple criteria (time period, form type and CIK). The crawler is capable of restoring the original files (html, jpg, pdf, ...) from the filing and saving these using your preferred file name pattern.


## Features

This project makes it easy to:
* Search the EDGAR database
* Download index files based on your searches
* Download filings based in your searches using multithreading to speed up the process
* Keep the filings either in raw format as obtained from the server or as orgininal documents (html, jpg)
* Use your own pattern for file names to suit your need

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
from edgarsearch import edgarsearch
```

### Use

Defining a search, downloading index files and filings, and extracting original files requires only 3 commands.
Example:

```shell
import edgarsearch.edgarsearch as es
if __name__ == '__main__':
    # Define a search by passing the start and end of the sample period, the sample size
    # as well as the desired formtype (and using defaults for the other values)
    search = es.Search("20151001",
                       "20161231",
                       sample_size=200,
                       filter_formtype=["8-K"])

    # Get the index file based on the defined search
    search.download_index()

    # Download the filings
    search.download_filings("months", 1, text_only=True,
							chunk_size=100)
```
## Contributing

If you'd like to contribute, please fork the repository and make changes as
you'd like. Pull requests are warmly welcome.

## Licensing

This project is licensed under the MIT License
