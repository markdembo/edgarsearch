"""Crawl EDGAR database to download index files and filings.

Example:
    import edgarsearch.edgarsearch
    search = edgarsearch.edgarsearch.Search("20151001",
                                            "20161231",
                                            sample_size=200,
                                            filter_formtype=["8-K"])
    search.download_index()
    search.safe_download("months", 1, text_only=True,
                         fname_form="%Y/%m/%Y%m_%company",
                         chunk_size=100)

Todo:
    *  Add proper exception handling
    *  Add rollback functions if an error occurs
    *  Add testing

"""
import datetime
import edgarsearch.indexhandler as ih
import edgarsearch.filingsbatch as fb
import pandas as pd
from tqdm import tqdm


class Search(object):
    """Search of the EDGAR database.

    Attributes:
        sample_start (str):  Start date for filings in sample.
            The valid format is "YYYYMMDD".
        sample_end (str): End date for filings in sample.
            The valid format is "YYYYMMDD".
        sample_size: (int): Number of samples in scope. If -1, no limit is set.
            Default to -1.
        filter_formtype (list of str, optional): Filter based on filings type.
            Example:["8-K, 10-K"]. Defaults to None.
        filter_CIK (list of str, optional):Filter based on CIK.
            Example: ["12345678", "98765432"]. Defaults to None.
        dir_work (str): Working subdirectory for all saved data.
            Defaults to "edgar/".
        sub_index (str): Subdirectory in dir_work for saved index data.
            Defaults to "index/".
        sub_filings (str): Subdirectory in dir_work for saved filings data.
            Defaults to "filings".
        edgar_url (str): URL to EDGAR server
            Defaults to  "https://www.sec.gov/Archives/".

    """

    def __init__(self, sample_start, sample_end, sample_size=-1, *,
                 filter_formtype=None, filter_CIK=None, dir_work="edgar/",
                 sub_index="index/", sub_filings="filings/",
                 edgar_url="https://www.sec.gov/Archives/"):
        """Create new EDGAR search object."""
        self.dir_work = dir_work
        self.sub_index = sub_index
        self.sub_filings = sub_filings
        self.edgar_url = edgar_url
        try:
            sample_start = datetime.datetime.strptime(sample_start, "%Y%m%d")
            sample_end = datetime.datetime.strptime(sample_end, "%Y%m%d")
        except ValueError:
            print("Dates must be in YYYYMMDD format.")

        if sample_start > sample_end:
            raise ValueError("Sample start must be prior to sample end")
        self.sample_start = sample_start
        self.sample_end = sample_end
        self.filter_formtype = filter_formtype
        self.filter_CIK = filter_CIK
        self.sample_size = sample_size

    def download_index(self):
        """Download the index of the corresponding search.

        Args:
            None

        Returns:
            None

        Raises:
            None

        """
        e_index = ih.EdgarIndex(self.sample_start, self.sample_end,
                                self.dir_work, self.sub_index,
                                self.edgar_url)
        e_index.download()
        e_index.consolidate()
        self.full_index = e_index.cons_index
        e_index.filter(self.sample_start, self.sample_end,
                       self.filter_formtype,
                       self.filter_CIK)
        filt_index = e_index.filtered_index

        if self.sample_size > 0:
            self.cur_index = filt_index.sample(self.sample_size)
        else:
            self.cur_index = filt_index

    def download_filings(self, index=None, raw=False, text_only=True,
                         chunk_size=100, disable_progressbar=False, **kwargs):
        """Process download requests in chunks.

        The method will execute the following steps:
            1. Split urls into chunks
            For each chunk:
            2. Download the filings from the server and store the .txt files
               temporaryly
            If raw = False:
            3. Extract the containing files from the .txt files
            4. Fix broken image paths in documents
            5. Delete temporary .txt files
            6. Store information about stored documents

        Args:
            urls (list of str): URLs of EDGAR filings to process.
            index (pandas dataframe): Index dataframe to be downloaded.
                If none, self.cur_index will be used. Defaults to None.
            raw (bool): If true, the original .txt files from the EDGAR server
                will be stored. If false, the containing documents will be
                extracted and stored. Defaults to False.
            chunk_size (int): Number of filings to process in only iteration.
                The bigger the chunk, the bigger the temporary file cache.
                Defaults to 100.
        Keyword Args:
            text_only (bool): If True, only html and txt files are saved.
                All other (media) files are discarded. Defaults to True.
            fname_form (str): String with the filename format.
                Possible parameters:
                * %org - orignal filename on server
                * %company - Company Name
                * All date variables based on strftime.
                  See: http://strftime.org/
                Defaults to "%Y%m%d_%company_".

        Returns:
            None

        Raises:
            None

        """
        if index is None:
            df = self.cur_index
        else:
            df = index

        # Check if chunk_size is reasonable and adjust if not
        length = df.shape[0]
        if chunk_size > length:
            chunk_size = length

        # Create chunks and prepare empty output DataFrames
        c_list = [df.iloc[i:i + chunk_size, :]
                  for i in range(0, length, chunk_size)]
        final_tmp_f = pd.DataFrame()
        final_docs = pd.DataFrame()

        # Print information to user
        print("Total filings to download: %s" % length)
        print("Number of batches: %s (containing %s filings each)"
              % (len(c_list), chunk_size))
        print("Progress:")

        # Iterate over chunks, while showing a progess bar
        for index_chunk in tqdm(c_list, disable=disable_progressbar):
            # Download the files from the server
            batch = fb.Batch(index_chunk, dir_work=self.dir_work,
                             sub_filings=self.sub_filings,
                             edgar_url=self.edgar_url, **kwargs)
            batch.download(disable_progressbar)

            # If raw is False, process the downloaded filins
            if raw is False:
                batch.splitfiles(**kwargs)
                documents = batch.docs
                batch.replace_img()
                batch.delete_tempfiles()
                final_docs = pd.concat([final_docs, documents])
            tmp_files = batch.temp_files
            final_tmp_f = pd.concat([final_tmp_f, tmp_files])

        self.temp_files = final_tmp_f
        self.docs = final_docs

    def safe_download(self, safemode_type="num", safemode_val=10000, **kwargs):
        """Run the data pipeline to download index and fillings data.

        Args:
            safemode_type (str, optional): Defines the safe mode to be used.
                Possible values:
                * "None": The full sample will be downloaded
                * "num" : Split sample based on the number of samples.
                * "years": Split sample based on sample years.
                * "months": Split sample based on sample months.
                Defaults to "num".
            safemode_val (int, optional): Value for the safe mode.
                If safe_mode is "num": Number of samples per subsample.
                If safe_mode is "years": Number of years per subsample.
                If safe_mode is "months": Number of months per subsample.
                Defaults to 10000.
        Keyword arguments:
            raw (bool): If true, the original .txt files from the EDGAR server
                will be stored. If false, the containing documents will be
                extracted and stored. Defaults to False.
            text_only (bool): If True, only html and txt files are saved.
                All other (media) files are discarded. Defaults to True.
            chunk_size (int): Number of filings to process in only iteration.
                The bigger the chunk, the bigger the temporary file cache.
                Defaults to 100.
            fname_form (str): String with the filename format.
                Possible parameters:
                * %org - orignal filename on server
                * %company - Company Name
                * All date variables based on strftime.
                  See: http://strftime.org/
                Defaults to "%Y%m%d_%company_".
        Returns:
            None

        Raises:
            None

        """
        fulldf = self.cur_index
        if safemode_type == "num":
            # Split sample into subsamples based on sample size
            for x in range(0, fulldf.shape[0], safemode_val):
                limit = min(fulldf.shape[0], x + safemode_val)
                tempdf = fulldf.iloc[x:limit, :]
                tqdm.write("Download sample %s-%s from total sample(size: %s)"
                           % (x, limit, fulldf.shape[0]))
                self.download_filings(index=tempdf, **kwargs)
                fname = (
                    "filings_"
                    + str(x)
                    + "_"
                    + str(limit)
                    + ".csv"
                )
                self.docs.to_csv(self.dir_work + fname, encoding="utf-8")

        elif safemode_type == "years":
            # Split sample into subsamples based on years in sample period
            year_s = self.sample_start.year
            year_e = self.sample_end.year
            for period in range(year_s, year_e + 1, safemode_val):
                end_year = min(year_e, period + safemode_val - 1)
                tempdf = fulldf.loc[((fulldf.date >= str(period)) &
                                     (fulldf.date <= str(end_year + 1)))]
                tqdm.write("Download sample %s-%s from total sample %s-%s"
                           % (period, end_year, year_s, year_e))
                self.download_filings(index=tempdf, **kwargs)
                self.docs.to_csv("filings_"
                                 + str(period)
                                 + "_"
                                 + str(end_year)
                                 + ".csv")
                if period == end_year:
                    fname = "filings_" + str(period) + ".csv"
                else:
                    fname = (
                        "filings_"
                        + str(period)
                        + "_"
                        + str(end_year)
                        + ".csv"
                    )
                self.docs.to_csv(self.dir_work + fname, encoding="utf-8")
        elif safemode_type == "months":
            # Split sample into subsamples based on months in sample period
            starty = self.sample_start.year
            startm = self.sample_start.month
            endy = self.sample_end.year
            endm = self.sample_end.month
            startdate = str(starty) + "-" + str(startm).zfill(2)
            enddate = str(endy) + "-" + str(endm).zfill(2)
            for year in range(starty, endy + 1):
                if year != starty:
                    start = 1
                else:
                    start = startm

                if year != endy:
                    end = 13
                else:
                    end = endm + 1
                for month in range(start, end, safemode_val):
                    limit = min(end, month + safemode_val)
                    start = str(year) + "-" + str(month).zfill(2)
                    if limit < 13:
                        stop = str(year) + "-" + str(limit).zfill(2)
                    else:
                        stop = str(year + 1) + "-" + str(limit - 12).zfill(2)

                    limit_d = min(end, month + safemode_val) - 1
                    if limit_d < 13:
                        stop_d = str(year) + "-" + str(limit_d).zfill(2)
                    else:
                        stop_d = (str(year + 1)
                                  + "-"
                                  + str(limit_d - 12).zfill(2)
                                  )
                    print("%s - %s" % (start, stop_d))

                    tempdf = fulldf.loc[((fulldf.date >= str(start)) &
                                         (fulldf.date < str(stop)))]
                    tqdm.write(("Download filings of period %s - %s from "
                               "total sample period %s - %s")
                               % (start, stop_d, startdate, enddate))
                    self.download_filings(index=tempdf, **kwargs)
                    if start == stop_d:
                        fname = "filings_" + str(start) + ".csv"
                    else:
                        fname = (
                            "filings_"
                            + str(start)
                            + "_"
                            + str(stop_d)
                            + ".csv"
                        )
                    self.docs.to_csv(self.dir_work + fname, encoding="utf-8")
