"""Collection of useful tools.

This module contains a collection of useful tools used in a wide variety of
settings.

Currently implemented:
    - Fuzzy-matching of columns from a pandas Dataframe

"""

import os
import string
import glob

def getalpha(x):
    """Convert integer to alphabetic characters.

    Args:
    x           Integer values

    Return:
    String of alphabetic equivalent to integer
    """
    result = ""
    if x // 26 > 0:
        result += getalpha((x // 26)-1)
        result += string.ascii_uppercase[(x % 26)]
    else:
        result += string.ascii_uppercase[(x % 26)]
    return result


def finduniquefilename(fname, mode="alpha", exact=True):
    """Return unique file name if file with original file name already exists.

    Args:
    fname       Filename to be checked
    mode        String setting the mode.
                Possible values:
                "alpha" will add alphabetical suffixes
                "num"  will add numerical suffixes
                default("alpha")
    exact       If true, check for the exact same file will be made
                If false, check whether a file with the same pattern exists

    Return:
    Unique filename
    Augment
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
