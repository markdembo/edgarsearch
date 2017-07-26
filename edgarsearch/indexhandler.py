"""EGDAR index downloader.

This module downloads relevant index files from the EGDAR database,
consolidates these. Moreover, filters are applied to only return relevant
results.

Functions in this module:
    download
    consolidates
    filter
"""

import urllib.request
import urllib.error
import os.path
import pandas as pd


class EdgarIndex(object):
    """Index of edgarfilings.

    Attributes:
        sample_start (datetime): Start date for the filings in sample.
        sample_end (datetime): End date for the filings in sample.
        dir_work (str): Path to working directory.
        sub_index (str): Path to subdirectory in working directory.
        edgar_url (str): URL to EDGAR archive parent folder on server.

    """

    def __init__(self, sample_start, sample_end,
                 dir_work, sub_index, edgar_url):
        """Class construnctor."""
        self.sample_start = sample_start
        self.sample_end = sample_end
        self.dir_work = dir_work
        self.sub_index = sub_index
        self.edgar_url = edgar_url

    def download(self):
        """Download index files from the EDGAR database.

        Args:
            None

        Returns:
            None

        Raises:
            None

        """
        url_start = "edgar/full-index/"
        url_end = "/form.idx"

        # Exclude quarters which are not in sample
        start_excl = []
        if self.sample_start.month > 3:
            start_excl.append(1)
        if self.sample_start.month > 6:
            start_excl.append(2)
        if self.sample_start.month > 9:
            start_excl.append(3)

        end_excl = []
        if self.sample_end.month < 10:
            end_excl.append(4)
        if self.sample_end.month < 7:
            end_excl.append(3)
        if self.sample_end.month < 4:
            end_excl.append(2)

        # For each quarter in each year in sample, check whether quarter is in
        # sample. If so download the index file if it does not already exist
        for year in range(self.sample_start.year, self.sample_end.year + 1):
            for quarter in range(1, 5):
                if (year == self.sample_start.year) & (quarter in start_excl):
                    continue
                elif (year == self.sample_end.year) & (quarter in end_excl):
                    continue
                else:
                    url = (self.edgar_url
                           + url_start
                           + str(year)
                           + "/QTR"
                           + str(quarter)
                           + url_end
                           )
                    fname = (self.dir_work
                             + self.sub_index
                             + str(year)
                             + "_"
                             + str(quarter)
                             + ".txt"
                             )
                    if os.path.isdir(os.path.dirname(fname)) is False:
                        os.makedirs(os.path.dirname(fname))
                    if os.path.isfile(fname) is False:
                        try:
                            urllib.request.urlretrieve(url, fname)
                        except urllib.error.HTTPError as e:
                            if e.code == 404:
                                print(("%s not on server!", url))
                            else:
                                print(e)

    def consolidate(self):
        """Consolidate index files and filter for desired form type.

        Args:
            None

        Returns:
            None

        Raises:
            None

        """
        index_files = os.listdir(self.dir_work + self.sub_index)
        result = pd.DataFrame()

        if len(index_files) == 0:
            print("No index files found. Download index files first")
            return None

        for indexf in index_files:
            indexdf = pd.read_fwf(self.dir_work + self.sub_index + indexf,
                                  widths=[12, 62, 12, 12, 52],
                                  skiprows=8,
                                  comment="---")
            indexdf["date"] = pd.to_datetime(indexdf["Date Filed"])
            result = result.append(indexdf)

        self.cons_index = result

    def filter(self, sample_start, sample_end, filter_formtype, filter_CIK):
        """Filter the index based on date, form type and/or CIK.

        Args:
            sample_start (datetime): Start date for the filings in sample.
            sample_end (datetime): End date for the filings in sample.
            filter_formtype (list of str, optional): SEC form types to include.
                None deactives the filter. Defaults to none.
            filter_CIK (list of str, optional): Company CIKs to include.
                None deactives the filter. Defaults to None.

        Returns:
            None

        Raises:
            None

        """
        # Filter based on sample period
        filterdf = self.cons_index.loc[(self.cons_index.date >= sample_start) &
                                       (self.cons_index.date <= sample_end)]

        # Filter based on form type
        if filter_formtype is not None:
            filterdf = filterdf[filterdf["Form Type"].isin(filter_formtype)]

        # Filter based on CIK
        if filter_CIK is not None:
            filterdf = filterdf[filterdf["CIK"].isin(filter_CIK)]

        self.filtered_index = filterdf
