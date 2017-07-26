"""

This a sample script to showcase the egdarsearch script.

For function defintion and possible parameters check out definition in
the edgarsearch.py file.

"""
import edgarsearch.edgarsearch

if __name__ == '__main__':
    # Setup the basical variables for the following commands (with defaults)
    my_edgar = edgarsearch.edgarsearch.edgar()
    # Define a search by passing the start and end of the sample period,
    # as well as the desired formtype

    my_edgar.definesearch("20150101", "20150731", filter_formtype=["8-K"])
    # Get the index file based on the defined search
    my_edgar.getindex()

    # Get a sample of 10 filings (including all media data) from the defined
    # search and store these using the desired file name pattern
    my_edgar.getfilings(text_only=False, sample_size=10,
                        fname_form="%Y/%m/%Y%m_%company")

    # Display the pandas df containg all the downloaded filings documents
    my_edgar.cur_filings
