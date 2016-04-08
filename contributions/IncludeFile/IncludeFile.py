#! /usr/bin/env python

"""
    MoinMoin - IncludeFile Macro

    Copyright (c) 2001 by Charles Bevali DHL Systems Inc 
                          <Charles.Bevali@systems.dhl.com>
    All rights reserved, see COPYING for details.

    This macro inserts a file-upload box or the uploaded file in the 
    body of a message, if it is a jpg or gif, or a link to the file  otherwise.

    This Macro requires the use of the UploadFile.cgi script

    The UploadFile.cgi script should be located in cgi-bin path so it can
    be executed, and the location of the script has to be set in the parameter

    Before to run it set the parameters:

    FILE_PATH:  path to the same place
    
    URL_PATH:   relative URL to the place you want to store the files

    UPLOAD_URL: URL to the UploadFile.cgi script

    ICON_URL:   URL to the icon you want to use for marking links

    $Id: IncludeFile.py,v 1.2 2004/01/30 21:29:58 thomaswaldmann Exp $
"""

###############################################################################
# PARAMETERS
FILE_PATH='/local/webserver/html/atpFiles/WikiWiki'   # Path to file storage
URL_PATH='/atpFiles/WikiWiki'                         # URL to file storage
UPLOAD_URL='/cgi-bin/MoinMoin/macro/UploadFile.cgi'   # URL to Upload script
ICON_URL="/wiki/classic/img/moin-www.png"            # Icon for links

###############################################################################
# Imports
import sys, cgi, re, os, string

##############################################################################
# Statics
_args_re_pattern = r'((?P<hquote>[\'"])(?P<htext>.+?)(?P=hquote))|'

# input form for the upload case
inputForm='<p><form method="POST" enctype="multipart/form-data" action="%s"> Locate file for "%s": <input type=file name=upfile><input type=hidden name=fileName value="%s"> <input type=submit value="Upload file"></form><p>' 

# use to detect images
imageTypes= ['.gif','.jpg', '.jpeg', '.png']

# Used to translate names into OS compliant names
charTrans = string.maketrans(' /\\:\'&<>?#$%*@~`|','______[]_________') 

INVALID_ARGUMENT=\
  '<p><strong class="error">Invalid IncludeFile arguments "%s"!</strong></p>'

##############################################################################
# execute
def execute(macro, text, args_re=re.compile(_args_re_pattern)):
    # if no args given, Error
    if text is None:
         return INVALID_ARGUMENT % (": Need a file name")

    args = args_re.match(text)
    if not args:
        return INVALID_ARGUMENT % (text,)

    file_desc = args.group('htext')
    fileName = string.translate(file_desc, charTrans)

    fname = '%s/%s' % (FILE_PATH, fileName)
    uname = '%s/%s' % (URL_PATH, fileName)

    try:
        f = open( fname, 'r' )
    except IOError: return inputForm % (UPLOAD_URL, file_desc , fileName)

    ( root, ext ) = os.path.splitext( fileName )
    
    try:
       imageTypes.index(string.lower(ext))
    except ValueError: return '<img src=%s> <a href=%s>%s</a>' \
                               % (ICON_URL, uname, file_desc)

    return '<img src=%s alt=%s>' % (uname, file_desc)

