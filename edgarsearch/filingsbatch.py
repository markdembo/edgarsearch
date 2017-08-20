"""Filings downloader and cleaner.

This module downloads filings from the EDGAR database and splits the filings
into multiple files.

Example:
    batch = fb.Batch(indexdf, dir_work="edgar/",
                     sub_filings="filings/",
                     edgar_url="https://www.sec.gov/Archives/")
    batch.download()
    batch.splitfiles()
    batch.replace_img()
    batch.delete_tempfiles()
    batch.docs

"""
import pandas as pd
import multiprocessing as mp
import edgarsearch.mpworker as mpw
import edgarsearch.tools as t
import re
import uu
import os
import datetime
import itertools
import io
import time
from tqdm import tqdm


class Batch(object):
    """Batch of filings.

    Attributes:
        index_slice (pandas dataframe): From indexhandler
        show_progess (bool): If true, a progressbar on file level will be
            displayed. Defaults to True.
        dir_work: (str): Working directory for all saved data.
            Defaults to "edgar/".
        sub_filings (str): Subdirectory for filings data.
            Defaults to "sub_filings".
        edgar_url (str): URL to EDGAR server
        timeout (int): Number of seconds to wait for the download to complete
            before the download attempt is counted as failed.
            Defaults to 30 seconds.
        attempts (int): Number of tries to download files
            Defaults to 3.

    """

    def __init__(self, index_slice, show_progess=True,
                 dir_work="edgar/", sub_filings="filings/",
                 edgar_url="https://www.sec.gov/Archives/",
                 timeout_limit=30, sleep_between_attempts=5,
                 attempts_max=3, **kwargs):
        """Class construnctor."""
        self.index_slice = index_slice
        self.show_progress = show_progess
        self.dir_work = dir_work
        self.sub_filings = sub_filings
        self.edgar_url = edgar_url
        self.timeout_limit = timeout_limit
        self.attempts_max = attempts_max
        self.sleep_between_attempts = sleep_between_attempts

        # List of str from filings index slice
        self.url_list = index_slice["File Name"].tolist()

    def collect(self, result):
        """Collect the results from the worker.

        Filter the results from the filings downloader and append to either the
        result list or error list.

        Args:
            result (list of str/int): Output from the singledownload worker.

        Returns:
            None

        Raises:
            None

        """
        if result[2] != "Error":
            self.results.append(result)
            if self.show_progress:
                self.bar.update(1)
        else:
            self.errors.append(result)

    def download(self, disable_progressbar=False):
        """Download all filings from a list of urls.

        Returns:
            None

        Raises:s
            None

        """
        # Create empty lists for errors and results
        self.errors = []
        self.results = []
        # Store the original URLs and set attemps = 0
        attempt = 0
        urls_queue = self.url_list
        # Init the second (lower) progress bar
        if self.show_progress:
            self.bar = tqdm(total=len(self.url_list),
                            disable=disable_progressbar,
                            )

        # If not all filins are downloaded yet and the attempts are below
        # three then try to download
        while (len(self.results) < len(self.url_list) and
               attempt < self.attempts_max - 1):
            # Use multiprocessing pool to download files
            mplist = list(itertools.product(urls_queue,
                                            [self.edgar_url],
                                            [self.dir_work],
                                            [self.sub_filings],
                                            ))
            pool = mp.Pool()
            for x in mplist:
                pool.apply_async(mpw.singledownload, x, callback=self.collect)
            pool.close()
            pool.join()

            # Check if errors occured and deal with these
            if len(self.errors) > 0:
                tqdm.write("Attempt %s: %s out of %s downloads failed."
                           % (attempt + 1,
                              len(self.errors),
                              len(self.url_list))
                           )
                tqdm.write("Attempt %s to download the filings "
                           "will start shortly."
                           % (attempt + 2))
                urls_queue = [item[0] for item in self.errors]
                self.errors = []
                attempt += 1
                time.sleep(self.sleep_between_attempts)
        # Handling unsuccesful attempts
        if (len(self.results) < len(self.url_list) and
                attempt >= self.attempts_max):
            tqdm.write("The final attempt was unsuccesful. "
                       "%s out %s files could not be downloaded."
                       % ((len(self.url_list) - len(self.result)),
                          len(self.url_list)))
        # Output if an error occured, but it could be fixed
        elif attempt > 0:
            tqdm.write("Attempt %s: Success. %s out %s files were downloaded."
                       % (attempt + 1, len(self.results), len(self.url_list)))
        # Create a pandas df with the filings' files information
        try:
            self.temp_files = pd.DataFrame(self.results,
                                           columns=["url",
                                                    "temp_fname",
                                                    "dt_accessed",
                                                    ])
            self.temp_files = self.temp_files.merge(self.index_slice,
                                                    left_on="url",
                                                    right_on="File Name")
        except Exception as e:
            tqdm.write(e)
        # Close the second (lower) progress bar
        if self.show_progress:
            self.bar.close()

    def splitfiles(self, text_only=True, **kwargs):
        """Extract the original documents from the temporary file from EDGAR.

        The archieved filings on EDGAR contain multiple files bundled in a
        .txt-file. This method splits the files into its original components.

        Args:
            text_only (bool): If True, only html and txt files are saved.
                All other (media) files are discarded. Defaults to True.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            None

        Raises:
            None

        """
        result = pd.DataFrame(columns=["url",
                                       "seq",
                                       "server_fname",
                                       "type",
                                       "desc",
                                       "local_fname",
                                       ])
        # Iterate over all documents to split files
        for index, row in self.temp_files.iterrows():
            # Get get filename and make sure path exists
            temp_fname = self.dir_work + self.sub_filings + row["temp_fname"]
            fname_part = create_filename(row, **kwargs)
            fname_full = self.dir_work + self.sub_filings + str(fname_part)
            fname_full = t.finduniquefname(fname_full, exact=False, **kwargs)
            path = os.path.dirname(fname_full)
            if os.path.isdir(path) is False:
                os.makedirs(path)

            # Open the temporary file and read the content
            with open(temp_fname) as f:
                txt = f.read()

            # Extract the filing metadata, write to file & append to DataFrame
            m_sec_header = re.search("<SEC-HEADER>.*</SEC-HEADER>",
                                     txt,
                                     re.DOTALL)
            b_sec_header = m_sec_header.group(0)
            local_fname = fname_full + "header.txt"
            with open(local_fname, "w") as out:
                out.write(b_sec_header)

            result.loc[result.shape[0]] = ([row["url"],
                                            0,
                                            "HEADER",
                                            "SEC Header",
                                            "Header file",
                                            local_fname])

            # Extract all other document parts
            splits = txt.split("<DOCUMENT>")[1:]
            # For each documents path: Extract information, save to file and
            # append to dataframe; depending on text_only only save text or all
            # information
            for i in splits:
                text_startpos = i.find("<TEXT>\n") + 7
                text_endpos = i.find("</TEXT") - 1
                text = i[text_startpos:text_endpos]

                search = ("<TYPE>(?P<TYPE>.+?)[\\n]+?"
                          "<SEQUENCE>(?P<SEQ>.+?)[\\n]+"
                          "<FILENAME>(?P<FNAME>.+?)[\\n]"
                          "(<DESCRIPTION>(?P<DESC>.+?)[\\n])?")
                try:
                    info = re.search(search, i, re.MULTILINE).groupdict()
                except:
                    print(i)
                    break
                if info["TYPE"] != "GRAPHIC":
                    local_fname = fname_full + str(info["SEQ"]) + ".html"
                    with open(local_fname, "w") as out:
                        out.write(text)
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
        self.docs = result

    def replace_img(self):
        """Replace image path in documents with local filename.

        Args:
            None

        Returns:
            None

        Raises:
            None

        """
        for url in self.docs.url.unique():
            extract_full = self.docs.loc[self.docs.url == url]
            extract_graphic = extract_full.loc[extract_full.type == "GRAPHIC"]
            extract_other = extract_full.loc[extract_full.type != "GRAPHIC"]
            if extract_graphic.shape[0] > 0:
                for index, row in extract_other.iterrows():
                    with open(row["local_fname"], "r") as f:
                        txt = f.read()
                    local = extract_graphic.local_fname.values
                    server = extract_graphic.server_fname.values
                    for i in range(len(local)):
                        txt = txt.replace(server[i], local[i].split("/")[-1])
                    with open(row["local_fname"], "w") as f:
                        f.write(txt)

    def delete_tempfiles(self):
        """Delete temporary raw downloaded files.

        Args:
            None

        Returns:
            None

        Raises:
            None

        """
        for index, row in self.temp_files.iterrows():
            fname = self.dir_work + self.sub_filings + row["temp_fname"]
            try:
                os.remove(fname)
            except:
                time.sleep(3)
                os.remove(fname)


def create_filename(row, fname_form="%Y%m%d_%company_", **kwargs):
    """Create filename for local EDGAR filing' files.

    Args:
         row (pandas series): Contains the columns "Date Filed",
            "Company Name" and "url".
         fname_form (str): String with the filename format.
            Possible parameters:
            * %org - orignal filename on server
            * %company - Company Name
            * All date variables based on strftime.
              See: http://strftime.org/
            Defaults to "%Y%m%d_%company_".
         **kwargs: Arbitrary keyword arguments.

    Returns:
         fname (str): The filename for the specific filing.

    Raises:
        None

    """
    # Extract the useful parts from the original filename on server
    splits = row["url"].split("/")
    org = splits[2] + "_" + splits[3].split(".")[0]

    # Extract unwanted characters from the company name
    company = (row["Company Name"]
               .replace(" ", "")
               .replace(",", "")
               .replace(".", "")
               .replace("/", "")
               .replace("\\", "")
               .lower()
               )
    # Replace the parameters with real values
    fname = fname_form.replace("%org", org).replace("%company", company)
    tdate = datetime.datetime.strptime(row["Date Filed"], "%Y-%m-%d")
    while fname.find("%") >= 0:
        char = "%" + fname[fname.find("%") + 1]
        fname = fname.replace(char, tdate.strftime(char))
    return fname
