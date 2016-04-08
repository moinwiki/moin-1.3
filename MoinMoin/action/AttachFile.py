"""
    MoinMoin - AttachFile action

    Copyright (c) 2001 by Ken Sugino (sugino@mediaone.net)
    Copyright (c) 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This action lets a page have multiple attachment files.
    It creates a folder <data>/pages/<pagename>/attachments
    and keeps everything in there.

    Form values: action=Attachment
    1. with no 'do' key: returns file upload form
    2. do=attach: accept file upload and saves the file in
       ../attachment/pagename/
    3. /pagename/fname?action=Attachment&do=get[&mimetype=type]:
       return contents of the attachment file with the name fname.
    4. /pataname/fname, do=view[&mimetype=type]:create a page
       to view the content of the file

    To insert an attachment into the page, use the "attachment:" pseudo
    schema.  

    $Id: AttachFile.py,v 1.36 2002/05/10 11:39:01 jhermann Exp $
"""

import cgi, os, mimetypes, string, sys, time, urllib
from MoinMoin import config, user, util, wikiutil, webapi
from MoinMoin.Page import Page
from MoinMoin.i18n import _

action_name = string.split(__name__, '.')[-1]
htdocs_access = isinstance(config.attachments, type({}))


#############################################################################
### External interface - these are called from the core code
#############################################################################

def getAttachDir(pagename):
    """ Get directory where attachments for page `pagename` are stored.
    """
    pagename = wikiutil.quoteFilename(pagename)
    if htdocs_access:
        # direct file access via webserver, from public htdocs area
        return os.path.join(config.attachments['dir'], pagename, "attachments")
    else:
        # send file via CGI, from page storage area
        return os.path.join(config.data_dir, "pages", pagename, "attachments")


def getAttachUrl(pagename, filename, addts=0):
    """ Get URL that points to attachment `filename` of page `pagename`.

        If 'addts' is true, a timestamp with the file's modification time
        is added, so that browsers reload a changed file.
    """
    if htdocs_access:
        # direct file access via webserver
        timestamp = ''
        if addts:
            try:
                timestamp = '?ts=%s' % os.path.getmtime(
                    os.path.join(getAttachDir(pagename), filename))
            except IOError:
                pass

        return "%s/%s/attachments/%s%s" % (
            config.attachments['url'], wikiutil.quoteFilename(pagename),
            urllib.quote_plus(filename), timestamp)
    else:
        # send file via CGI
        return "%s/%s?action=%s&do=get&target=%s" % (
            webapi.getBaseURL(), wikiutil.quoteWikiname(pagename),
            action_name, urllib.quote_plus(filename) )


def info(pagename, request):
    """ Generate snippet with info on the attachment for page `pagename`.
    """
    attach_dir = getAttachDir(pagename)
    files = []
    if os.path.isdir(attach_dir):
        files = os.listdir(attach_dir)
    print _('There are <a href="%(link)s">%(count)s attachment(s)</a> stored for this page.') % {
        'count': len(files),
        'link': Page(pagename).url("action=AttachFile")
    }
    print "<p>"


#############################################################################
### Internal helpers
#############################################################################

def _addLogEntry(action, pagename, filename):
    """ Add an entry to the edit log on uploads and deletes.

        `action` should be "ATTNEW" or "ATTDEL"
    """
    from MoinMoin import editlog
    log = editlog.makeLogStore()
    remote_name = os.environ.get('REMOTE_ADDR', '')
    log.addEntry(pagename, remote_name, time.time(),
        urllib.quote(filename), action)


def _access_file(pagename, request):
    """ Check form parameter `target` and return a tuple of
        `(filename, filepath)` for an existing attachment.

        Return `(None, None)` if an error occurs.
    """
    error = None
    if not request.form.getvalue('target', ''):
        error = _("<b>Filename of attachment not specified!</b>")
    else:
        filename = wikiutil.taintfilename(request.form['target'].value)
        fpath = os.path.join(getAttachDir(pagename), filename)

        if os.path.isfile(fpath):
            return (filename, fpath)
        error = _("<b>Attachment '%(filename)s' does not exist!</b>") % locals()

    error_msg(pagename, request, error)
    return (None, None)


def _get_filelist(request, pagename):
    # access directory
    attach_dir = getAttachDir(pagename)
    files = []
    if os.path.isdir(attach_dir):
        files = os.listdir(attach_dir)

    str = ""
    if files:
        str = str + _("<p>"
            "To refer to attachments on a page, use <b><tt>attachment:filename</tt></b>, \n"
            "as shown below in the list of files. \n"
            "Do <b>NOT</b> use the URL of the <tt>[get]</tt> link, \n"
            "since this is subject to change and can break easily.</p>"
        )
        str = str + "<ul>"

        label_del = _("del")
        label_get = _("get")
        label_edit = _("edit")
        label_view = _("view")

        for file in files:
            fsize = os.stat(os.path.join(attach_dir,file))[6] # in byte
            fsize = float(int(float(fsize)/102.4))/10.0
            baseurl = webapi.getBaseURL()
            action = action_name
            urlpagename = wikiutil.quoteWikiname(pagename)
            urlfile = urllib.quote_plus(file)

            del_link = ''
            if request.user.may.delete:
                del_link = '<A HREF="%(baseurl)s/%(pagename)s' \
                    '?action=%(action)s&do=del&target=%(urlfile)s">%(label_del)s</A>&nbsp;| ' % locals()

            base, ext = os.path.splitext(file)
            get_url = getAttachUrl(pagename, file)
            if ext == '.draw':
                viewlink = '<A HREF="%(baseurl)s/%(urlpagename)s?action=%(action)s&drawing=%(base)s">%(label_edit)s</A>' % locals()
            else:
                viewlink = '<A HREF="%(baseurl)s/%(urlpagename)s?action=%(action)s&do=view&target=%(urlfile)s">%(label_view)s</A>' % locals()

            str = str + ('<li>[%(del_link)s'
                '<A HREF="%(get_url)s">%(label_get)s</A>&nbsp;| %(viewlink)s]'
                ' (%(fsize)g KB) attachment:<b>%(file)s</b></li>') % locals()
        str = str + "</ul>"
    else:
        str = '%s<p>%s</p>' % (str, _("No attachments stored for %(pagename)s") % locals())

    return str
        
    
def error_msg(pagename, request, msg):
    Page(pagename).send_page(request, msg=msg)


#############################################################################
### Create parts of the Web interface
#############################################################################

def send_hotdraw(pagename, request):
    now = time.time()
    pubpath = config.url_prefix + "/applets/TWikiDrawPlugin"
    drawpath = getAttachUrl(pagename, request.form['drawing'].value + '.draw')
    gifpath = getAttachUrl(pagename, request.form['drawing'].value + '.gif')
    pagelink = wikiutil.quoteWikiname(pagename) + "?action=AttachFile&ts=%s" % now 
    savelink = Page(pagename).url()
    #savelink = '/cgi-bin/dumpform.bat'

    if htdocs_access:
        timestamp = '?ts=%s' % now
    else:
        timestamp = '&ts=%s' % now

    print _("<h2>Edit drawing</h2>")
    print """
<p>
<img src="%(gifpath)s%(timestamp)s" border=2>
<applet code="CH.ifa.draw.twiki.TWikiDraw.class"
        archive="%(pubpath)s/twikidraw.jar" width="100%%" height=40>
<param name="drawpath" value="%(drawpath)s">
<param name="gifpath"  value="%(gifpath)s">
<param name="savepath" value="%(savelink)s">
<param name="viewpath" value="%(pagelink)s">
<param name="helppath" value="%(pagelink)s">
<b>NOTE:</b> You need a Java enabled browser to edit the drawing example.
</applet>
<p>""" % locals()


def send_uploadform(pagename, request):
    """ Send the HTML code for the list of already stored attachments and
        the file upload form.
    """
    print _("<h2>Attached Files</h2>")
    print _get_filelist(request, pagename)

    if not request.user.may.edit:
        print '<p>%s</p>' % _('<b>You are not allowed to upload files.</b>')
        return

    if request.form.getvalue('drawing', None):
        send_hotdraw(pagename, request)
        return

    print _("""
<h2>New Attachment</h2>
<p>An upload will never overwrite an existing file. If there is a name
conflict, you have to rename the file that you want to upload.
Otherwise, if "Rename to" is left blank, the original filename will be used.</p>
""")
    print """
<form action="%(baseurl)s/%(pagename)s" method="POST" enctype="multipart/form-data">
<input type="hidden" name="action" value="%(action_name)s">
<input type="hidden" name="do" value="upload">
<table border="0">
<tr><td><b>%(upload_label_file)s</b></td>
<td><input type="file" name="file" size="50"></td></tr>
<tr><td><b>%(upload_label_mime)s</b></td>
<td><input type="text" name="mime" size="50"></td></tr>
<tr><td><b>%(upload_label_rename)s</b></td>
<td><input type="text" name="rename" size="50" value="%(rename)s"></td></tr>
<tr><td></td><td><input type="submit" value="%(upload_button)s"></td></tr>
</table>
</form>
""" % {
    'baseurl': webapi.getBaseURL(),
    'pagename': wikiutil.quoteWikiname(pagename),
    'action_name': action_name,
    'upload_label_file': _('File to upload'),
    'upload_label_mime': _('MIME Type (optional)'),
    'upload_label_rename': _('Rename to (optional)'),
    'rename': request.form.getvalue('rename', ''),
    'upload_button': _(' Upload '),
}


#############################################################################
### Web interface for file upload, viewing and deletion
#############################################################################

def execute(pagename, request):
    """ Main dispatcher for the 'AttachFile' action.
    """
    msg = None
    if action_name in config.excluded_actions:
        msg = _('<b>File attachments are not allowed in this wiki!</b>')
    elif request.form.has_key('filepath'):
        save_drawing(pagename, request)
        webapi.http_headers(request)
        print "OK"
    elif not request.form.has_key('do'):
        upload_form(pagename, request)
    elif request.form['do'].value == 'upload':
        if request.user.may.edit:
            do_upload(pagename, request)
        else:
            msg = _('<b>You are not allowed to upload files.</b>')
    elif request.form['do'].value == 'del':
        if request.user.may.delete:
            del_file(pagename, request)
        else:
            msg = _('<b>You are not allowed to delete attachments.</b>')
    elif request.form['do'].value == 'get':
        get_file(pagename, request)
    elif request.form['do'].value == 'view':
        view_file(pagename, request)
    else:
        msg = _('<b>Unsupported upload action: %s</b>') % (request.form['do'].value,)

    if msg:
        error_msg(pagename, request, msg)


def upload_form(pagename, request, msg=''):
    webapi.http_headers(request)
    wikiutil.send_title(_('Attachments for "%(pagename)s"') % locals(), pagename=pagename, msg=msg)
    send_uploadform(pagename, request)
    wikiutil.send_footer(request, pagename, showpage=1)

    
def do_upload(pagename, request):
    # check file & mimetype
    fileitem = request.form['file']
    if not fileitem.file:
        error_msg(pagename, request,
            _("<b>Filename of attachment not specified!</b>"))
        return

    # get directory, and possibly create it
    attach_dir = getAttachDir(pagename)
    if not os.path.isdir(attach_dir): 
        os.makedirs(attach_dir, 0777 & config.umask)

    # make filename
    filename = fileitem.filename
    rename = ''
    if request.form.has_key('rename'):
        rename = string.strip(request.form['rename'].value)

    target = filename
    target = string.replace(target, ':', '/')
    target = string.replace(target, '\\', '/')
    target = string.split(target, '/')[-1]
    if rename:
        target = string.strip(rename)

    target = wikiutil.taintfilename(target)

    # set mimetype from extension, or from given mimetype
    type, encoding = mimetypes.guess_type(target)
    if not type:
        ext = None
        if request.form.has_key('mime'):
            ext = mimetypes.guess_extension(request.form['mime'].value)
        if not ext:
            type, encoding = mimetypes.guess_type(filename)
            if type:
                ext = mimetypes.guess_extension(type)
            else:
                ext = ''
        target = target + ext
    
    # save file
    fpath = os.path.join(attach_dir, target)
    if os.path.exists(fpath):
        msg = _("Attachment '%(target)s' (remote name '%(filename)s') already exists.") % locals()
    else:
        content = fileitem.file.read()
        stream = open(fpath, 'wb')
        try:
            stream.write(content)
        finally:
            stream.close()
        os.chmod(fpath, 0666 & config.umask)

        bytes = len(content)
        msg = _("Attachment '%(target)s' (remote name '%(filename)s')"
                " with %(bytes)d bytes saved.") % locals()
        _addLogEntry('ATTNEW', pagename, target)

    # return attachment list
    upload_form(pagename, request, msg)


def save_drawing(pagename, request):
    filename = request.form['filepath'].filename
    content = request.form['filepath'].value

    if htdocs_access:
        basepath, ext = os.path.splitext(filename)
        basename = os.path.basename(basepath)

        # check that we get a valid path
        if basepath != getAttachUrl(pagename, basename):
            # die hard on saver if he cheats
            print >>sys.stderr, "save_drawing: tainted path '%s', aborting!" % filename
            sys.exit(1)
    else:
        # get file information from URL-like filename
        import urlparse
        parts = urlparse.urlparse(filename)
        args = util.parseQueryString(parts[4])

        basename, ext = os.path.splitext(wikiutil.taintfilename(args['target']))
        basepath = getAttachUrl(pagename, basename)

    # get directory, and possibly create it
    attach_dir = getAttachDir(pagename)
    if not os.path.isdir(attach_dir): 
        os.makedirs(attach_dir, 0777 & config.umask)

    if ext == '.draw':
        _addLogEntry('ATTDRW', pagename, basename + ext)

    savepath = os.path.join(getAttachDir(pagename), basename + ext)
    file = open(savepath, 'wb')
    try:
        file.write(content)
    finally:
        file.close()



def del_file(pagename, request):
    filename, fpath = _access_file(pagename, request)
    if not filename: return # error msg already sent in _access_file
    
    # delete file
    os.remove(fpath)
    _addLogEntry('ATTDEL', pagename, filename)

    upload_form(pagename, request, msg=_("Attachment '%(filename)s' deleted.") % locals())


def get_file(pagename, request):
    import shutil

    filename, fpath = _access_file(pagename, request)
    if not filename: return # error msg already sent in _access_file
    
    # get mimetype
    type, enc = mimetypes.guess_type(filename)
    if not type:
        type = "application/octet-stream"

    # send header
    webapi.http_headers(request, [
        "Content-Type: %s" % type,
        "Content-Length: %d" % os.path.getsize(fpath),
        "Content-Disposition: attachment; filename=%s" % filename, 
    ])
    
    # send data
    shutil.copyfileobj(open(fpath, 'rb'), sys.stdout, 8192)

    sys.exit(0)


def send_viewfile(pagename, request):
    filename, fpath = _access_file(pagename, request)
    if not filename: return

    print _("<h2>Attachment '%(filename)s'</h2>") % locals()
    
    type, enc = mimetypes.guess_type(filename)
    if type:
        if type[:5] == 'image':
            timestamp = htdocs_access and "?%s" % time.time() or ''
            print '<img src="%s%s" alt="%s">' % (
                getAttachUrl(pagename, filename), timestamp, cgi.escape(filename, 1))
            return
        elif type[:4] == 'text': 
            sys.stdout.write("<pre>")
            sys.stdout.write(cgi.escape(open(fpath, 'r').read()))
            sys.stdout.write("</pre>")
            return

    print _("<p>Unknown file type, cannot display this attachment inline.</p>")
    print '<a href="%s">%s</a>' % (
        getAttachUrl(pagename, filename), cgi.escape(filename))

    
def view_file(pagename, request):
    filename, fpath = _access_file(pagename, request)
    if not filename: return
    
    # send header & title
    webapi.http_headers(request)
    wikiutil.send_title(_('attachment:%(filename)s of %(pagename)s') % locals(),
        pagename=pagename)

    # send body
    send_viewfile(pagename, request)
    send_uploadform(pagename, request)

    # send footer
    wikiutil.send_footer(request, pagename)

