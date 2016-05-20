#!/usr/bin/env python
"""
Convert data in encoding src_enc to encoding dst_enc, both specified
on command line. Data is read from standard input and written to
standard output.

Usage:

    ./recode.py src_enc dst_enc < src  > dst

Example:

    # Using non utf-8 editor to edit utf-8 file:

    # Make a working copy using iso-8859-1 encoding
    ./recode.py utf-8 iso-8859-1 < de.po > de-iso1.po

    # Use non-utf8 editor
    $EDITOR de-iso1.po

    # Recode back to utf-8
    ./recode.py iso-8859-1 utf-8 < de-iso1.po > de-utf8.po

    # Review changes and replace original if everything is ok
    diff de.po de-utf8.po | less
    mv de-utf8.po de.po

"""

import sys


def error(msg):
    sys.stderr.write(msg + '\n')
    

try:
    cmd, src_enc, dst_enc = sys.argv

    for line in sys.stdin:
        line = unicode(line, src_enc).encode(dst_enc)
        sys.stdout.write(line)

except UnicodeError, err:
    error("Can't recode: %s" % str(err))
except LookupError, err:
    error(str(err))
except ValueError:
    error("Wrong number of arguments")
    error(__doc__)


