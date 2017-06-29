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


def download(sample_start, sample_end, folder, sub):
    """Download index files from the EDGAR database.

    Args:
    sample_start        Start date for filings in sample
                        Datetime objects
    sample_end          End date for filings in sample
                        Datetime objects
    folder              Path to work working directory
    sub                 Path to subdirectory in working directory

    Return:
    None
    """
    url_start = "https://www.sec.gov/Archives/edgar/full-index/"
    url_end = "/form.idx"

    start_excl = []
    if sample_start.month > 3:
        start_excl.append(1)
    if sample_start.month > 6:
        start_excl.append(2)
    if sample_start.month > 9:
        start_excl.append(3)

    end_excl = []
    if sample_end.month < 10:
        end_excl.append(4)
    if sample_end.month < 7:
        end_excl.append(3)
    if sample_end.month < 4:
        end_excl.append(2)

    for year in range(sample_start.year, sample_end.year+1):
        for quarter in range(1, 5):
            if (year == sample_start.year) & (quarter in start_excl):
                continue
            elif (year == sample_end.year) & (quarter in end_excl):
                continue
            else:
                url = url_start + str(year) + "/QTR" + str(quarter) + url_end
                fname = (
                            folder
                            + sub
                            + str(year)
                            + "_"
                            + str(quarter)
                            + ".txt"
                            )
                if os.path.isdir(os.path.split(fname)[0]) is False:
                    os.makedirs(os.path.split(fname)[0])
                if os.path.isfile(fname) is False:
                    try:
                        urllib.request.urlretrieve(url, fname)
                    except urllib.error.HTTPError as e:
                        if e.code == 404:
                            print(("%s not on server!", url))
                        else:
                            print(e)


def consolidate(folder, sub):
    """Consolidate index files and filter for desired form type.

    Args:
    folder              Path to work working directory
    sub                 Path to subdirectory in working directory

    Return:
        Pandas Dataframe of the consolidated index

    """
    index_files = os.listdir(folder + sub)
    result = pd.DataFrame()

    if len(index_files) == 0:
        print("No index files found. Download index files first")
        return None

    for indexf in index_files:
        indexdf = pd.read_fwf(folder + sub + indexf,
                              widths=[12, 62, 12, 12, 52],
                              skiprows=8,
                              comment="---")
        indexdf["date"] = pd.to_datetime(indexdf["Date Filed"])
        result = result.append(indexdf)

    return result


def filter(index, sample_start, sample_end, *,
           filter_formtype=None, filter_CIK=None):
    """Filter index based on form type and/or CIK.

    Args:
    sample_start        Start date for filings in sample
                        Datetime objects
    sample_end          End date for filings in sample
                        Datetime objects
    index               Pandas df containg the full index of the sample period
    filter_formtype     Optional argument to filter based on filings type
                        List with strings e.g. ["8-K, 10-K"]
    filter_CIK          Optional argument to filter based on CIK
                        List with strings e.g. ["12345678", "98765432"]

    Return:
        Pandas Dataframe of the filtered index

    """
    f_period = index.loc[(index.date > sample_start) &
                         (index.date < sample_end)]

    f_type = pd.DataFrame()
    if filter_formtype is not None:
        for formtype in filter_formtype:
            f_type = f_type.append((f_period
                                    .loc[f_period["Form Type"] == formtype]
                                    )
                                   )
    else:
        f_type = index

    f_CIK = pd.DataFrame()
    if filter_CIK is not None:
        for CIK in filter_CIK:
            f_CIK = f_CIK.append(f_type.loc[f_type["CIK"] == CIK])
    else:
        f_CIK = f_type
    return f_CIK
