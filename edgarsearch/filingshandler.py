"""Filings downloader and cleaner.

This module downloads filings from the EDGAR database and splits the filings
into multiple files.

"""

import pandas as pd
import multiprocessing as mp
import filingshandler_worker as fhw
import tools as t
import re
import uu
import os
import datetime
import itertools
import io

# Local Variables


def multidownload(urls, folder="data/", sub="filings/",
                  edgar_url="https://www.sec.gov/Archives/", **kwargs):
    """Download all filings from a list of URLs.

    Args:
    urls:   List of relative paths to filings in the EDGAR archives
    folder: Path to work working directory (default = data/)
    sub:    Path to subdirectory in working directory (default = filings/)
    edgar_url: URL to archive parent folder on edgar server
               (defaut: "https://www.sec.gov/Archives/")
    Return:
    None

    TODO:
    Make it server friendly with timeouts
    """
    mplist = list(itertools.product(urls, [edgar_url], [folder], [sub]))
    with mp.Pool(mp.cpu_count()) as p:
        result = p.starmap(fhw.singledownload, mplist)
    index = pd.DataFrame(result, columns=["url", "temp_fname", "dt_accessed"])
    return index


def create_filename(row, fname_form="%Y%m%d_%company_", **kwargs):
    """Create filenames for local EDGAR filing documents.

    Args:
    row         Row of Pandas df containing the columns "Date Filed",
                "Company Name" and "url" from the EDGAR index files
    fname_form  String with the filename format.
                Possible variables:
                %org - orignal file name on server
                %company - Company Name
                All date variables based on strftime.
                See: http://strftime.org/
                (default: "%Y%m%d_%company_")
    Return:
    filename as string
    """
    splits = row["url"].split("/")
    org = splits[2] + "_" + splits[3].split(".")[0]

    company = (row["Company Name"]
               .replace(" ", "")
               .replace(",", "")
               .replace(".", "")
               .replace("/", "")
               .replace("\\", "")
               .lower()
               )
    fname = fname_form.replace("%org", org).replace("%company", company)
    tdate = datetime.datetime.strptime(row["Date Filed"], "%Y-%m-%d")
    while fname.find("%") >= 0:
        char = "%" + fname[fname.find("%")+1]
        fname = fname.replace(char, tdate.strftime(char))
    return fname


def splitfiles(docs, folder="data/", sub="filings/", text_only=True, **kwargs):
    """Extract the original documents from the downloaded .txt file from EDGAR.

    Args:
    row         Row from local index Pandas df containing "filename"
    folder      Path of work dir (default = "data/")
    sub         Path of sub dir in work dir (default = "filings/")
    fname_form  String with the filename format.
                Possible variables:
                %org - orignal file name on server
                %company - Company Name
                All date variables based on strftime.
                See: http://strftime.org/
    text_only   If True, only html and txt files are saved. All other types of
                contents such as images and pdfs are discarded
                (default: True)
    Return:     Index of local files
    """
    result = pd.DataFrame(columns=[
                                 "url",
                                 "seq",
                                 "server_fname",
                                 "type",
                                 "desc",
                                 "local_fname",
                                 ])
    for index, row in docs.iterrows():
        tmp_fname = folder + sub + row["temp_fname"]
        fname_part = create_filename(row, **kwargs)
        fname_full = folder + sub + str(fname_part)
        fname_full = t.finduniquefilename(fname_full, exact=False)
        path = fname_full[0:fname_full.rfind("/")]
        if os.path.isdir(path) is False:
            os.makedirs(path)
        f = open(tmp_fname)
        txt = f.read()
        f.close()
        m_sec_header = re.search("<SEC-HEADER>.*</SEC-HEADER>",
                                 txt,
                                 re.DOTALL)
        b_sec_header = m_sec_header.group(0)
        local_fname = fname_full + "header.txt"
        out = open(local_fname, "w")
        out.write(b_sec_header)
        out.close()
        result.loc[result.shape[0]] = ([row["url"],
                                        0,
                                        "HEADER",
                                        "SEC Header",
                                        "Header file",
                                        local_fname])
        starts = ([a.end() for a in list(re.finditer("<DOCUMENT>", txt))])
        ends = ([a.start() for a in list(re.finditer("</DOCUMENT>", txt))])

        for i in range(len(starts)):
            content = txt[starts[i]:ends[i]]
            text = content[content.find("<TEXT>\n")+7:content.find("</TEXT")-1]

            search = ("<TYPE>(?P<TYPE>.+?)[\\n]+?"
                      "<SEQUENCE>(?P<SEQ>.+?)[\\n]+"
                      "<FILENAME>(?P<FNAME>.+?)[\\n]"
                      "(<DESCRIPTION>(?P<DESC>.+?)[\\n])?")
            try:
                info = re.search(search, content, re.MULTILINE).groupdict()
            except:
                print(content)
                break
            if info["TYPE"] != "GRAPHIC":
                local_fname = fname_full + str(info["SEQ"]) + ".html"
                out = open(local_fname, "w")
                out.write(text)
                out.close()
            else:
                if text_only is True:
                    break
                local_fname = fname_full + str(info["SEQ"]) + ".jpg"
                f = io.BytesIO(bytes(text, encoding="ascii"))
                uu.decode(f, local_fname, quiet=True)
                f.close()

            result.loc[result.shape[0]] = ([row["url"],
                                           info["SEQ"],
                                           info["FNAME"],
                                           info["TYPE"],
                                           info["DESC"],
                                           local_fname])
    return result


def replace_img(docs):
    """Replace image path in documents with local filename.

    Args:
    docs:       Pandas df containing all the index of all documents
                belonging to a filing.

    Return:
    None

    """
    for url in docs.url.unique():
        extract_full = docs.loc[docs.url == url]
        extract_graphic = extract_full.loc[extract_full.type == "GRAPHIC"]
        extract_other = extract_full.loc[extract_full.type != "GRAPHIC"]
        if extract_graphic.shape[0] > 0:
            for index, row in extract_other.iterrows():
                f = open(row["local_fname"], "r")
                txt = f.read()
                local = extract_graphic.local_fname.values
                server = extract_graphic.server_fname.values
                for i in range(len(local)):
                    txt = txt.replace(server[i], local[i].split("/")[-1])
                f.close()
                f = open(row["local_fname"], "w")
                f.write(txt)
                f.close


def delfiles(docs, folder="data/", sub="filings/", **kwards):
    """Delete temp raw downloaded files.

    Args:
    row:     Row of Pandas df containing the column "temp_fname"

    Return:
    None
    """
    for index, row in docs.iterrows():
        os.remove(folder + sub + row["temp_fname"])


def batch_process(urls, index, raw=False,
                  text_only=True, chunk_size=100, **kwargs):
    """Execute the defined pipeline in chunks.

    Args:
    urls        List of urls of EDGAR filings to process
    raw         Bool to define wheter the raw filings shall be kept
                or the documents shall be extracted
                (default=False)
    text_only   Bool to defined whether only text files shall be storage or
                non-text files such as images as well
                (default=True)
    chunk_size  Integer for the size of each chunk to process. The bigger the
                chunk, the bigger the temporary file cache.
                (default=100)

    Returns:
    Pandas df containg an index of all raw files
    Pandas df containg an index of all seperated files

    """
    if text_only is False:
        space_req = len(urls) / 1000
        string = ("Saving non-text files may take a lot of space."
                  "The estimated required space is %0.1f GB."
                  " Do you want to continue? [Y]es or [N]o? " % space_req)
        while True:
            check = input(string).lower()
            if ((check == "y") | (check == "yes") |
               (check == "no") | (check == "n")):
                break
        if (check == "no") | (check == "n"):
            return None, None
    if chunk_size > len(urls):
        chunk_size = len(urls)
    c_list = [urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)]
    final_tmp_f = pd.DataFrame()
    final_docs = pd.DataFrame()
    for urls_sub in c_list:
        tmp_files = (multidownload(urls_sub, **kwargs)
                     .merge(index, left_on="url", right_on="File Name"))
        if raw is False:
            documents = splitfiles(tmp_files, text_only=text_only, **kwargs)
            replace_img(documents)
            delfiles(tmp_files, **kwargs)
            final_docs = pd.concat([final_docs, documents])
        final_tmp_f = pd.concat([final_tmp_f, tmp_files])
    return final_tmp_f.reset_index(), final_docs.reset_index()
