"""Crawl EDGAR database to download index files and filings.

Contains the edgar class.

Sample script:
my_edgar = edgar()
my_edgar.definesearch("20150101", "20151231", filter_formtype=["8-K"])
my_edgar.getindex()
my_edgar.getfilings(text_only=False, sample_size=10,
                    fname_form="%Y/%m/%Y%m_%company")
my_edgar.cur_filings

"""
import datetime
import indexhandler as ih
import filingshandler as fh


class edgar:
    """Class for EDGAR searches.

    Contains public functions to download and search index files and also

    """

    def __init__(self,
                 dir_work="edgar/",
                 sub_index="index/",
                 sub_filings="filings/",
                 edgar_url="https://www.sec.gov/Archives/"):
        """Create new EDGAR search object.

        Args:
        dir_work:           Working subdirectory for all saved data
                            (default: "edgar/")
        sub_index:          Subdirectory in dir_work for saved index data
                            (default: "index/")
        sub_filings:        Subdirectory in dir_work for saved filings data
                            (default: "filings")
        edgar_url:          URL to EDGAR server
                            (default: "https://www.sec.gov/Archives/")
        """
        self.dir_work = dir_work
        self.sub_index = sub_index
        self.sub_filings = sub_filings
        self.edgar_url = edgar_url

    def definesearch(self, sample_start, sample_end, *,
                     filter_formtype=None, filter_CIK=None):
        """Set parameters for new search request.

        Args:
        sample_start        Start date for filings in sample
                            String in the format "YYYYMMDD"
        sample_end          End date for filings in sample
                            String in the format "YYYYMMDD"
        filter_formtype     Optional argument to filter based on filings type
                            List with strings e.g. ["8-K, 10-K"]
        filter_CIK          Optional argument to filter based on CIK
                            List with strings e.g. ["12345678", "98765432"]

        """
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

    def getindex(self):
        """Download and store the relevant index.

        Args:
        None

        Return:
        Pandas Dataframe with the corresponding index
        """
        try:
            self.cur_index = ih.filter(self.fullindex,
                                       self.sample_start,
                                       self.sample_end,
                                       filter_formtype=self.filter_formtype,
                                       filter_CIK=self.filter_CIK)
        except:
            ih.download(self.sample_start, self.sample_end,
                        self.dir_work, self.sub_index)
            self.fullindex = ih.consolidate(self.dir_work, self.sub_index)
            self.cur_index = ih.filter(self.fullindex,
                                       self.sample_start,
                                       self.sample_end,
                                       filter_formtype=self.filter_formtype,
                                       filter_CIK=self.filter_CIK)
        return self.cur_index

    def getfilings(self, sample_size=-1, **kwargs):
        """Download the filings matching the search criteria.

        Args:
        sample_size Number of samples to obtain from the selected search.
                    -1 equals the full sample.
                    (default =-1)
        fname_form  String with the filename format.
                    Possible variables:
                    %org - orignal file name on server
                    %company - Company Name
                    All date variables based on strftime.
                    See: http://strftime.org/
                    (default: "%Y%m%d_%company_")
        text_only   If True, only html and txt files are saved. All other types
                    of contents such as images and PDFs are discarded
        raw         Bool to define wheter the raw filings shall be kept
                    or the documents shall be extracted
                    (default=False)
        chunk_size  Integer for the size of each chunk to process. The greater
                    the chunks, the larger the temporary file cache.
                    (default=100)

        Return:
        Pandas DF with the file list
        """
        try:
            if sample_size > 0:
                url_list = (
                            self.cur_index["File Name"]
                            .sample(sample_size)
                            .tolist()
                            )
            else:
                url_list = self.cur_index["File Name"].tolist()
        except:
            try:
                self.cur_index.shape[0] = 0
                print("Current query yields no result.")
            except:
                print("Search not defined or index not yet obtained.")

        tmp_files, *documents = fh.batch_process(url_list,
                                                 self.cur_index,
                                                 folder=self.dir_work,
                                                 sub=self.sub_filings,
                                                 edgar_url=self.edgar_url,
                                                 **kwargs)
        self.tmp_files = tmp_files
        self.cur_filings = documents
        return self.cur_filings
