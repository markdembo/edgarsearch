"""Useful tool collection.

Consists of the following functions:
    * getalpha: Convert integer to alphabetic character.
    * finduniquefilename: Find unique name if a file with the original filename
                          already exists.


Example:
    getalpha(0)  --> "A"
    getalpha(1)  --> "B"
    getalpha(27) --> "AB"
    finduniquefilename(ab, mode="alpha", exact=True):


Todo:
    *  None

"""

import os
import string
import glob


def getalpha(x):
    """Convert integer to alphabetic character.

    Assigns every integer to a alphabetic string.
    Examples for clarification:
        getalpha(0)  --> "A"
        getalpha(1)  --> "B"
        getalpha(27) --> "AB"

    Args:
        x (integer): Number to be converted

    Returns:
        result (String): Alphabetic equivalent to integer

    Raises:
        None

    """
    result = ""
    if x // 26 > 0:
        result += getalpha((x // 26)-1)
        result += string.ascii_uppercase[(x % 26)]
    else:
        result += string.ascii_uppercase[(x % 26)]
    return result


def finduniquefname(fname, mode="alpha", exact=True, **kwargs):
    """Find unique name if a file with the original file name already exists.

    Args:
        fname_form (String): Filename (incl. path) to be checked
        mode (String): Sets the mode for creating unique filenames.
            Possible values:
            * "alpha" will add alphabetical suffixes
            * "num"  will add numerical suffixes
            default("alpha")
        extract (Bool): If true, checks for the exact file name.
            If false, checks for the filename pattern
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        fname (String): Unique filename

    Raises:
        None

    """
    i = 0
    fpre, fsuf = os.path.splitext(fname)
    if exact is True:
        while os.path.isfile(fname):
            if mode == "alpha":
                fname = (
                         fpre
                         + getalpha(i)
                         + fsuf
                         )
            elif mode == "num":
                fname = (
                         fpre
                         + str(i)
                         + fsuf
                         )
            i += 1
    else:
        while len(glob.glob(fname + "*")) > 0:
            if mode == "alpha":
                fname = (
                         fpre
                         + getalpha(i)
                         + fsuf
                         )
            elif mode == "num":
                fname = (
                         fpre
                         + str(i)
                         + fsuf
                         )
            i += 1
    return(fname)
