"""Filings downloader.

This module downloads filings from the EDGAR database and extracts relevant
information from the filings.

"""
import urllib.request
import uuid
import datetime
import os


def singledownload(url, edgar_url="https://www.sec.gov/Archives/",
                   folder="data/", sub="filings/", **kwargs):
    """Download filings from the EDGAR database.

    Args:
        url: relative path in the EDGAR server
        edgar_url: URL to archive parent folder on edgar server
                   (defaut: "https://www.sec.gov/Archives/")
        folder: Path to work working directory (default = data/)
        sub: Path to subdirectory in working directory (default = filings/)
    Return:
        List of the downloaded url and the relative file path
    """
    full_url = edgar_url + url
    fname = str(uuid.uuid4()) + ".txt"
    txt = urllib.request.urlopen(full_url).read()
    if os.path.isdir(folder+sub) is False:
        os.makedirs(folder+sub)
    try:
        f = open(folder + sub + fname, 'x')
    except:
        f = open(folder + sub + fname, 'w+')
    f.write(txt.decode('utf-8'))
    f.close
    accessed = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    return [url, fname, accessed]
