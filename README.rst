Edgarsearch
===========

    Crawl EDGAR database to download index files and filings.

Use this crawler to download index files and filings from the SEC EGDAR
Database based on multiple criteria (time period, form type and CIK).
The crawler is capable of restoring the original files (html, jpg, pdf,
…) from the filing and saving these using your preferred file name
pattern.

Features
--------

This project makes it easy to:

-  Search the EDGAR database
-  Download index files based on your searches
-  Download filings based in your searches using multithreading to speed
   up the process
-  Keep the filings either in raw format as obtained from the server or
   as orgininal documents (html, jpg, pdf)
-  Use your own pattern for file names to suit your need

Getting started
---------------

Install
~~~~~~~

Simply install egdarsearch using pip:

.. code:: shell

    pip install edgarsearch

This code will install the edgarsearch package and its dependencies
(Pandas).

Import
~~~~~~

Import the package using

.. code:: shell

    import edgarsearch

Use
~~~

| Defining a search, downloading index files and filings, and extracting
  original files requires only 4 commands.
| Example:

.. code:: shell

    if __name__ == '__main__':
        # Setup the basical variables for the following commands (with defaults)
        my_edgar = edgarsearch.edgar()
        # Define a search by passing the start and end of the sample period,
        # as well as the desired formtype

        my_edgar.definesearch("20150101", "20150731", filter_formtype=["8-K"])
        # Get the index file based on the defined search
        my_index = my_edgar.getindex()

        # Get a sample of 10 filings (including all media data) from the defined
        # search and store these using the desired file name pattern
        my_edgar.getfilings(text_only=False, sample_size=100,
                            fname_form="%Y/%m/%Y%m_%company")

        # Display the pandas df containg all the downloaded filings documents
        my_filings = my_edgar.cur_filings

Contributing
------------

If you’d like to contribute, please fork the repository and make
changes as you’d like. Pull requests are warmly welcome.

Licensing
---------

This project is licensed under the MIT License
