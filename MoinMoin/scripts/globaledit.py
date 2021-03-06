"""
    Script for doing global changes to all pages in a wiki.

    You either need to have your wiki configs in sys.path or you
    need to invoke this script from the same directory.

    @copyright: 2004, Thomas Waldmann
    @license: GPL licensed, see COPYING for details
"""

debug = False

url = "moinmaster.wikiwikiweb.de/"

def do_edit(origtext):
    language_line = format_line = masterpage = None
    acl_lines = []
    master_lines = []
    pragma_lines = []
    comment_lines = []
    content_lines = []
    lines = origtext.splitlines()
    header = True
    for l in lines:
        if not l.startswith('#'):
            header = False
        if header:
            if l.startswith('#acl '):
                acl_lines.append(l)
            elif l.startswith('#language '):
                language_line = l
            elif l.startswith('#format '):
                format_line = l
            elif l.startswith('##master-page:'):
                masterpage = l.split(':',1)[1].strip()
                master_lines.append(l)
            elif l.startswith('##master-date:'):
                master_lines.append(l)
            elif l.startswith('##'):
                comment_lines.append(l)
            elif l.startswith('#'):
                pragma_lines.append(l)
        else:
            content_lines.append(l)

    if not language_line:
        language_line = '#language en'
    if not format_line:
        format_line = '#format wiki'
    if not acl_lines and (masterpage is None or
        masterpage not in ['FrontPage', 'WikiSandBox',] and not masterpage.endswith('Template')):
        acl_lines = ['#acl MoinPagesEditorGroup:read,write,delete,revert All:read']
    if not master_lines:
        master_lines = ['##master-page:Unknown-Page', '##master-date:Unknown-Date',]
    c1 = "## Please edit system and help pages ONLY in the moinmaster wiki! For more"
    c2 = "## information, please see MoinMaster:MoinPagesEditorGroup."
    if c1 in comment_lines:
        comment_lines.remove(c1)
    if c2 in comment_lines:
        comment_lines.remove(c2)
    comment_lines = [c1, c2, ] + comment_lines

    if content_lines and content_lines[-1].strip(): # not an empty line at EOF
        content_lines.append('')

    changedtext = comment_lines + master_lines + acl_lines + [format_line, language_line,] + pragma_lines + content_lines
    changedtext = '\n'.join(changedtext)
    return changedtext

if __name__ == '__main__':
    if debug:
        import codecs
        origtext = codecs.open('origtext', 'r', 'utf-8').read()
        origtext = origtext.replace('\r\n','\n')
        changedtext = do_edit(origtext)
        changedtext = changedtext.replace('\n','\r\n')
        f = codecs.open('changedtext', 'w', 'utf-8')
        f.write(changedtext)
        f.close()
    else:

        from MoinMoin import PageEditor, wikiutil
        from MoinMoin.request import RequestCLI

        request = RequestCLI(url=url)
        # Get all existing pages in the wiki
        pagelist = request.rootpage.getPageList(user='')

        for pagename in pagelist:
            request = RequestCLI(url=url, pagename=pagename.encode('utf-8'))
            p = PageEditor.PageEditor(request, pagename, do_editor_backup=0)
            origtext = p.get_raw_body()
            changedtext = do_edit(origtext)
            if changedtext and changedtext != origtext:
                print "Writing %s ..." % repr(pagename)
                p._write_file(changedtext)

