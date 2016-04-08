#! /usr/bin/env python

"""
    MoinMoin - UploadFile utility, to use with IncludeFile Macro 

    Copyright (c) 2001 by Charles Bevali DHL Systems Inc 
                          <Charles.Bevali@systems.dhl.com>

    All rights reserved, see COPYING for details.

    That utility is used by IncludeFile.py to upload a file at the
    designated location (see paramaters)

    It is recommended to locate that file in the macro folder.

    Before to runs it set the parameters:

    URL_PATH:  relative URL to the place you want to store the files

    FILE_PATH: path to the same place
    

    $Id: UploadFile.cgi,v 1.1 2001/11/09 00:25:21 jhermann Exp $
"""

############################################################################
# PARAMETERS
URL_PATH='/atpFiles/WikiWiki'
FILE_PATH='/local/webserver/html%s' % (URL_PATH)


############################################################################
# Imports
import sys, cgi, os

#############################################################################
## Uploading routine
def upload():

   form = cgi.FieldStorage()

   #cgi.print_environ()
   #cgi.print_form(form) 

   fileName=form['fileName'].value


   file = form["upfile"]

   if not file.file: 
      print 'Content-type: text/html'
      print
      print 'Content-type: text/html\n\n<html><h1>%s is not a file</h1>'
      print '<Type back to return to your page</html>' % (file)
      return

   tfname= '%s/%s' % (FILE_PATH, fileName)

   chunk='dummy'
   theFile=file.file
   tfile = os.open( tfname , os.O_WRONLY | os.O_CREAT )

   while chunk:
      chunk=theFile.read()
      os.write( tfile, chunk )

   print "Location: "+os.environ["HTTP_REFERER"]
   print
   return
   

############################################################################
# main

upload()
sys.exit(0)


