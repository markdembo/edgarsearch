"""Downloads filings from the EDGAR database.

Examples:
    simple:
    singledownload("edgar/data/1645148/0001213900-15-004775.txt")
    for slow internet connections:
    singledownload("edgar/data/1645148/0001213900-15-004775.txt", timeout=120)
    with different folder structure:
    singledownload("edgar/data/1645148/0001213900-15-004775.txt",
                   folder="myfolder/", sub="")

"""
import urllib.request
import uuid
import datetime
import os


def singledownload(url, edgar_url="https://www.sec.gov/Archives/",
                   folder="data/", sub="filings/", timeout=30):
    """Download filings from the EDGAR database.

    Args:
        url (str): Relative path on the EDGAR server.
        edgar_url (str): URL to EDGAR archive parent folder on server.
            Defaults to "https://www.sec.gov/Archives/".
        folder (str): Path to working directory. Defaults to "data/".
        sub (str): Path to subdirectory in working directory.
            Defaults to "filings/".
        timeout (int): Number of seconds to wait for the download to complete
            before the download attempt is counted as failed.
            Defaults to 30 seconds.

    Returns:
        result (list): Information on which was downloaded, the local filename
            and the date and time the file was downloaded.

    Raises:
        None

    """
    full_url = edgar_url + url
    fname = str(uuid.uuid4()) + ".txt"
    accessed = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    try:
        txt = urllib.request.urlopen(full_url, timeout=timeout).read()
    except Exception as e:
        return [url, e, "Error"]

    if os.path.isdir(folder + sub) is False:
        try:
            os.makedirs(folder + sub)
        except Exception as e:
            print(e)

    try:
        f = open(folder + sub + fname, 'x')
    except Exception:
        f = open(folder + sub + fname, 'w+')
    f.write(txt.decode('utf-8'))
    f.close
    result = [url, fname, accessed]
    return result
