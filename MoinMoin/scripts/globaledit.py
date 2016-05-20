"""
    Script for doing global changes to all pages in a wiki.

    You either need to have your wiki configs in sys.path or you
    need to invoke this script from the same directory.

    @copyright: 2004, Thomas Waldmann
    @license: GPL licensed, see COPYING for details
"""

url = "moinmaster.wikiwikiweb.de"

from MoinMoin import PageEditor, wikiutil
from MoinMoin.request import RequestCLI

def do_edit(origtext):
    changedtext = """#acl MoinPagesEditorGroup:read,write,delete,revert All:read
## Please edit system and help pages ONLY in the moinmaster wiki! For more
## information, please see MoinMaster:MoinPagesEditorGroup.
""" + origtext
    return changedtext
    
request = RequestCLI(url=url)
# Get all pages in the wiki
pagelist = request.rootpage.getPageList(user='')

for pagename in pagelist:
    request = RequestCLI(url=url, pagename=pagename)
    p = PageEditor.PageEditor(pagename, request, do_editor_backup=0)
    origtext = p.get_raw_body()
    changedtext = do_edit(origtext)
    if changedtext and changedtext != origtext:
        print "Writing %s ..." % repr(pagename)
        p._write_file(changedtext)


