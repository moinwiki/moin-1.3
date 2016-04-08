# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - AttachFile action

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

    @copyright: 2001 by Ken Sugino (sugino@mediaone.net)
    @copyright: 2001-2004 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import os, mimetypes, time, urllib
from MoinMoin import config, user, util, wikiutil
from MoinMoin.Page import Page
from MoinMoin.util import MoinMoinNoFooter, filesys

action_name = __name__.split('.')[-1]
htdocs_access = isinstance(config.attachments, type({}))


#############################################################################
### External interface - these are called from the core code
#############################################################################

def getBasePath():
    """ Get base path where page dirs for attachments are stored.
    """
    if htdocs_access:
        return config.attachments['dir']
    else:
        return os.path.join(config.data_dir, "pages")


def getAttachDir(pagename, create=0):
    """ Get directory where attachments for page `pagename` are stored.
    """
    if htdocs_access:
        # direct file access via webserver, from public htdocs area
        pagename = wikiutil.quoteFilename(pagename)
        attach_dir = os.path.join(config.attachments['dir'], pagename, "attachments")
    else:
        # send file via CGI, from page storage area
        attach_dir = wikiutil.getPagePath(pagename, "attachments", check_create=create)

    if create and not os.path.isdir(attach_dir): 
        filesys.makeDirs(attach_dir)

    return attach_dir


def getAttachUrl(pagename, filename, request, addts=0, escaped=0):
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

        url = "%s/%s/attachments/%s%s" % (
            config.attachments['url'], wikiutil.quoteFilename(pagename),
            urllib.quote(filename), timestamp)
    else:
        # send file via CGI
        url = "%s/%s?action=%s&do=get&target=%s" % (
            request.getScriptname(), wikiutil.quoteWikiname(pagename),
            action_name, urllib.quote_plus(filename) )

    if escaped:
        url = wikiutil.escape(url)
    return url

def getIndicator(request, pagename):
    """ Get an attachment indicator for a page (linked clip image) or
        an empty string if not attachments exist.
    """
    _ = request.getText
    attach_dir = getAttachDir(pagename)
    if not os.path.exists(attach_dir): return ''

    files = os.listdir(attach_dir)
    if not files: return ''

    attach_count = _('[%d attachments]') % len(files)
    attach_icon = request.theme.make_icon('attach', vars={ 'attach_count': attach_count })
    attach_link = wikiutil.link_tag(request,
        "%s?action=AttachFile" % wikiutil.quoteWikiname(pagename),
        attach_icon)

    return attach_link


def info(pagename, request):
    """ Generate snippet with info on the attachment for page `pagename`.
    """
    _ = request.getText

    attach_dir = getAttachDir(pagename)
    files = []
    if os.path.isdir(attach_dir):
        files = os.listdir(attach_dir)
    attach_info = _('There are <a href="%(link)s">%(count)s attachment(s)</a> stored for this page.') % {
        'count': len(files),
        'link': Page(pagename).url(request, "action=AttachFile")
    }
    return "\n<p>\n%s\n</p>\n" % attach_info


#############################################################################
### Internal helpers
#############################################################################

def _addLogEntry(request, action, pagename, filename):
    """ Add an entry to the edit log on uploads and deletes.

        `action` should be "ATTNEW" or "ATTDEL"
    """
    from MoinMoin.logfile import editlog
    log = editlog.EditLog()
    log.add(request, pagename, request.remote_addr, time.time(),
        urllib.quote(filename), action)


def _access_file(pagename, request):
    """ Check form parameter `target` and return a tuple of
        `(filename, filepath)` for an existing attachment.

        Return `(None, None)` if an error occurs.
    """
    _ = request.getText

    error = None
    if not request.form.get('target', [''])[0]:
        error = _("Filename of attachment not specified!")
    else:
        filename = wikiutil.taintfilename(request.form['target'][0])
        fpath = os.path.join(getAttachDir(pagename), filename)

        if os.path.isfile(fpath):
            return (filename, fpath)
        error = _("Attachment '%(filename)s' does not exist!") % {'filename': filename}

    error_msg(pagename, request, error)
    return (None, None)


def _build_filelist(request, pagename, showheader, readonly):
    _ = request.getText

    # access directory
    attach_dir = getAttachDir(pagename)
    files = []
    if os.path.isdir(attach_dir):
        files = os.listdir(attach_dir)
        files.sort()

    str = ""
    if files:
        if showheader:
            str = str + _("<p>"
                          "To refer to attachments on a page, use <strong><tt>attachment:filename</tt></strong>, \n"
                          "as shown below in the list of files. \n"
                          "Do <strong>NOT</strong> use the URL of the <tt>[get]</tt> link, \n"
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
            baseurl = request.getScriptname()
            action = action_name
            urlpagename = wikiutil.quoteWikiname(pagename)
            urlfile = urllib.quote_plus(file)

            base, ext = os.path.splitext(file)
            get_url = getAttachUrl(pagename, file, request, escaped=1)
            parmdict = {'baseurl': baseurl, 'urlpagename': urlpagename, 'action': action,
                        'urlfile': urlfile, 'label_del': label_del,
                        'base': base, 'label_edit': label_edit,
                        'label_view': label_view,
                        'get_url': get_url, 'label_get': label_get,
                        'file': file, 'fsize': fsize,
                        'pagename': pagename}
            
            del_link = ''
            if request.user.may.delete(pagename) and not readonly:
                del_link = '<a href="%(baseurl)s/%(urlpagename)s' \
                    '?action=%(action)s&amp;do=del&amp;target=%(urlfile)s">%(label_del)s</a>&nbsp;| ' % parmdict

            if ext == '.draw':
                viewlink = '<a href="%(baseurl)s/%(urlpagename)s?action=%(action)s&amp;drawing=%(base)s">%(label_edit)s</a>' % parmdict
            else:
                viewlink = '<a href="%(baseurl)s/%(urlpagename)s?action=%(action)s&amp;do=view&target=%(urlfile)s">%(label_view)s</a>' % parmdict

            parmdict['viewlink'] = viewlink
            parmdict['del_link'] = del_link
            str = str + ('<li>[%(del_link)s'
                '<a href="%(get_url)s">%(label_get)s</a>&nbsp;| %(viewlink)s]'
                ' (%(fsize)g KB) attachment:<strong>%(file)s</strong></li>') % parmdict
        str = str + "</ul>"
    else:
        if showheader:
            str = '%s<p>%s</p>' % (str, _("No attachments stored for %(pagename)s") % {'pagename': pagename})

    return str


def _get_filelist(request, pagename):
    return _build_filelist(request, pagename, 1, 0)


def error_msg(pagename, request, msg):
    Page(pagename).send_page(request, msg=msg)


#############################################################################
### Create parts of the Web interface
#############################################################################

def send_link_rel(request, pagename):
    attach_dir = getAttachDir(pagename)
    if os.path.isdir(attach_dir):
        files = os.listdir(attach_dir)
        files.sort()
        for file in files:
            get_url = getAttachUrl(pagename, file, request, escaped=1)
            request.write('<link rel="Appendix" title="%s" href="%s">\n' % (
                wikiutil.escape(file), get_url))


def send_hotdraw(pagename, request):
    _ = request.getText

    now = time.time()
    pubpath = config.url_prefix + "/applets/TWikiDrawPlugin"
    basename = request.form['drawing'][0]
    drawpath = getAttachUrl(pagename, request.form['drawing'][0] + '.draw', request, escaped=1)
    pngpath = getAttachUrl(pagename, request.form['drawing'][0] + '.png', request, escaped=1)
    pagelink = wikiutil.quoteWikiname(pagename) + "?action=AttachFile&amp;ts=%s" % now 
    savelink = Page(pagename).url(request) # XXX include target filename param here for twisted
                                           # request, {'savename': request.form['drawing'][0]+'.draw'}
    #savelink = '/cgi-bin/dumpform.bat'

    if htdocs_access:
        timestamp = '?ts=%s' % now
    else:
        timestamp = '&amp;ts=%s' % now

    request.write('<h2>' + _("Edit drawing") + '</h2>')
    request.write("""
<p>
<img src="%(pngpath)s%(timestamp)s">
<applet code="CH.ifa.draw.twiki.TWikiDraw.class"
        archive="%(pubpath)s/twikidraw.jar" width="640" height="480">
<param name="drawpath" value="%(drawpath)s">
<param name="pngpath"  value="%(pngpath)s">
<param name="savepath" value="%(savelink)s">
<param name="basename" value="%(basename)s">
<param name="viewpath" value="%(pagelink)s">
<param name="helppath" value="%(pagelink)s">
<strong>NOTE:</strong> You need a Java enabled browser to edit the drawing example.
</applet>
</p>""" % {
    'pngpath': pngpath, 'timestamp': timestamp,
    'pubpath': pubpath, 'drawpath': drawpath,
    'savelink': savelink, 'pagelink': pagelink,
    'basename': basename
})


def send_uploadform(pagename, request):
    """ Send the HTML code for the list of already stored attachments and
        the file upload form.
    """
    _ = request.getText
    
    if not request.user.may.read(pagename):
        request.write('<p>%s</p>' % _('You are not allowed to view this page.'))
        return

    request.write('<h2>' + _("Attached Files") + '</h2>')
    request.write(_get_filelist(request, pagename))

    if not request.user.may.edit(pagename):
        request.write('<p>%s</p>' % _('You are not allowed to attach a file to this page.'))
        return

    if request.form.get('drawing', [None])[0]:
        send_hotdraw(pagename, request)
        return

    request.write('<h2>' + _("New Attachment") + '</h2><p>' +
_("""An upload will never overwrite an existing file. If there is a name
conflict, you have to rename the file that you want to upload.
Otherwise, if "Rename to" is left blank, the original filename will be used.""") + '</p>')
    request.write("""
<form action="%(baseurl)s/%(pagename)s" method="POST" enctype="multipart/form-data">
<dl>
<dt>%(upload_label_file)s</dt>
<dd><input type="file" name="file" size="50"></dd>
<dt>%(upload_label_mime)s</dt>
<dd><input type="text" name="mime" size="50"></dd>
<dt>%(upload_label_rename)s</dt>
<dd><input type="text" name="rename" size="50" value="%(rename)s"></dd>
</dl>
<p>
<input type="hidden" name="action" value="%(action_name)s">
<input type="hidden" name="do" value="upload">
<input type="submit" value="%(upload_button)s">
</p>
</form>
""" % {
    'baseurl': request.getScriptname(),
    'pagename': wikiutil.quoteWikiname(pagename),
    'action_name': action_name,
    'upload_label_file': _('File to upload'),
    'upload_label_mime': _('MIME Type (optional)'),
    'upload_label_rename': _('Save as'),
    'rename': request.form.get('rename', [''])[0],
    'upload_button': _('Upload'),
})


#############################################################################
### Web interface for file upload, viewing and deletion
#############################################################################

def execute(pagename, request):
    """ Main dispatcher for the 'AttachFile' action.
    """
    _ = request.getText

    msg = None
    if action_name in config.excluded_actions:
        msg = _('File attachments are not allowed in this wiki!')
    elif request.form.has_key('filepath'):
        if request.user.may.edit(pagename):
            save_drawing(pagename, request)
            request.http_headers()
            request.write("OK")
        else:
            msg = _('You are not allowed to save a drawing on this page.')
    elif not request.form.has_key('do'):
        upload_form(pagename, request)
    elif request.form['do'][0] == 'upload':
        if request.user.may.edit(pagename):
            do_upload(pagename, request)
        else:
            msg = _('You are not allowed to attach a file to this page.')
    elif request.form['do'][0] == 'del':
        if request.user.may.delete(pagename):
            del_file(pagename, request)
        else:
            msg = _('You are not allowed to delete attachments on this page.')
    elif request.form['do'][0] == 'get':
        if request.user.may.read(pagename):
            get_file(pagename, request)
        else:
            msg = _('You are not allowed to get attachments from this page.')
    elif request.form['do'][0] == 'view':
        if request.user.may.read(pagename):
            view_file(pagename, request)
        else:
            msg = _('You are not allowed to view attachments of this page.')
    else:
        msg = _('Unsupported upload action: %s') % (request.form['do'][0],)

    if msg:
        error_msg(pagename, request, msg)


def upload_form(pagename, request, msg=''):
    _ = request.getText

    request.http_headers()
    wikiutil.send_title(request, _('Attachments for "%(pagename)s"') % {'pagename': pagename}, pagename=pagename, msg=msg)
    request.write('<div id="content">\n') # start content div
    send_uploadform(pagename, request)
    request.write('</div>\n') # end content div
    wikiutil.send_footer(request, pagename, showpage=1)

 
def do_upload(pagename, request):
    _ = request.getText

    # make filename
    filename = None
    if request.form.has_key('file__filename__'):
        filename = request.form['file__filename__']
    rename = None
    if request.form.has_key('rename'):
        rename = request.form['rename'][0].strip()

    # if we use twisted, "rename" field is NOT optional, because we
    # can't access the client filename
    if rename:
        filename = target = rename
    elif filename:
        target = filename
    else:
        error_msg(pagename, request, _("Filename of attachment not specified!"))
        return

    # get file content
    filecontent = request.form['file'][0]
    
    target = wikiutil.taintfilename(target)

    # set mimetype from extension, or from given mimetype
    type, encoding = mimetypes.guess_type(target)
    if not type:
        ext = None
        if request.form.has_key('mime'):
            ext = mimetypes.guess_extension(request.form['mime'][0])
        if not ext:
            type, encoding = mimetypes.guess_type(filename)
            if type:
                ext = mimetypes.guess_extension(type)
            else:
                ext = ''
        target = target + ext
    
    # get directory, and possibly create it
    attach_dir = getAttachDir(pagename, create=1)
    # save file
    fpath = os.path.join(attach_dir, target)
    if os.path.exists(fpath):
        msg = _("Attachment '%(target)s' (remote name '%(filename)s') already exists.") % {
            'target': target, 'filename': filename}
    else:
        stream = open(fpath, 'wb')
        try:
            stream.write(filecontent)
        finally:
            stream.close()
        os.chmod(fpath, 0666 & config.umask)

        bytes = len(filecontent)
        msg = _("Attachment '%(target)s' (remote name '%(filename)s')"
                " with %(bytes)d bytes saved.") % {
                'target': target, 'filename': filename, 'bytes': bytes}
        _addLogEntry(request, 'ATTNEW', pagename, target)

    # return attachment list
    upload_form(pagename, request, msg)


def save_drawing(pagename, request):
    from MoinMoin.util import web
    
    filename = request.form['filename'][0]
    filecontent = request.form['filepath'][0]

    # there should be no difference in filename parsing with or without
    # htdocs_access, cause the filename param is used
    basepath, basename = os.path.split(filename)
    basename, ext = os.path.splitext(basename)

    # get directory, and possibly create it
    attach_dir = getAttachDir(pagename, create=1)

    if ext == '.draw':
        _addLogEntry(request, 'ATTDRW', pagename, basename + ext)

    savepath = os.path.join(getAttachDir(pagename), basename + ext)
    if ext == '.map' and filecontent.strip()=='':
        # delete map file if it is empty
        os.unlink(savepath)
    else:
        file = open(savepath, 'wb')
        try:
            file.write(filecontent)
        finally:
            file.close()

    # touch attachment directory to invalidate cache if new map is saved
    if ext == '.map':
        os.utime(getAttachDir(pagename), None)

def del_file(pagename, request):
    _ = request.getText

    filename, fpath = _access_file(pagename, request)
    if not filename: return # error msg already sent in _access_file
    
    # delete file
    os.remove(fpath)
    _addLogEntry(request, 'ATTDEL', pagename, filename)

    upload_form(pagename, request, msg=_("Attachment '%(filename)s' deleted.") % {'filename': filename})


def get_file(pagename, request):
    import shutil

    filename, fpath = _access_file(pagename, request)
    if not filename: return # error msg already sent in _access_file
    
    # get mimetype
    type, enc = mimetypes.guess_type(filename)
    if not type:
        type = "application/octet-stream"

    # send header
    request.http_headers([
        "Content-Type: %s" % type,
        "Content-Length: %d" % os.path.getsize(fpath),
        "Content-Disposition: inline; filename=%s" % filename, 
    ])
    
    # send data
    shutil.copyfileobj(open(fpath, 'rb'), request, 8192)

    raise MoinMoinNoFooter


def send_viewfile(pagename, request):
    _ = request.getText

    filename, fpath = _access_file(pagename, request)
    if not filename: return

    request.write('<h2>' + _("Attachment '%(filename)s'") % {'filename': filename} + '</h2>')
    
    type, enc = mimetypes.guess_type(filename)
    if type:
        if type[:5] == 'image':
            timestamp = htdocs_access and "?%s" % time.time() or ''
            request.write('<img src="%s%s" alt="%s">' % (
                getAttachUrl(pagename, filename, request, escaped=1), timestamp, wikiutil.escape(filename, 1)))
            return
        elif type[:4] == 'text': 
            request.write("<pre>")
            request.write(wikiutil.escape(open(fpath, 'r').read()))
            request.write("</pre>")
            return

    request.write('<p>' + _("Unknown file type, cannot display this attachment inline.") + '</p>')
    request.write('<a href="%s">%s</a>' % (
        getAttachUrl(pagename, filename, request, escaped=1), wikiutil.escape(filename)))

    
def view_file(pagename, request):
    _ = request.getText

    filename, fpath = _access_file(pagename, request)
    if not filename: return
    
    # send header & title
    request.http_headers()
    wikiutil.send_title(request, _('attachment:%(filename)s of %(pagename)s') % {
        'filename': filename, 'pagename': pagename}, pagename=pagename)

    # send body
    request.write('<div id="content">\n') # start content div
    send_viewfile(pagename, request)
    send_uploadform(pagename, request)
    request.write('</div>\n') # end content div

    # send footer
    wikiutil.send_footer(request, pagename)


#############################################################################
### File attachment administration
#############################################################################

def do_admin_browser(request):
    """ Browser for SystemAdmin macro.
    """
    from MoinMoin.util.dataset import TupleDataset, Column
    _ = request.getText

    data = TupleDataset()
    data.columns = [
        Column('page', label=('Page')),
        Column('file', label=('Filename')),
        Column('size',  label=_('Size'), align='right'),
        Column('action', label=_('Action')),
    ]

    # iterate over pages that might have attachments
    pages = os.listdir(getBasePath())
    for pagename in pages:
        # check for attachments directory
        page_dir = getAttachDir(pagename)
        if os.path.isdir(page_dir):
            # iterate over files of the page
            files = os.listdir(page_dir)
            for filename in files:
                filepath = os.path.join(page_dir, filename)
                data.addRow((
                    Page(pagename).link_to(request, querystr="action=AttachFile"),
                    wikiutil.escape(filename),
                    os.path.getsize(filepath),
                    '',
                ))

    if data:
        from MoinMoin.widget.browser import DataBrowserWidget

        browser = DataBrowserWidget(request)
        browser.setData(data)
        return browser.toHTML()

    return ''

