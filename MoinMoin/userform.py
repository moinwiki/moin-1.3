"""
    MoinMoin - User Account Maintenance

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: userform.py,v 1.17 2002/04/24 20:11:21 jhermann Exp $
"""

# Imports
import os, string, time
from MoinMoin import config, user, util, webapi, wikiutil
from MoinMoin.i18n import _, languages

try:
    import Cookie
except ImportError:
    from MoinMoin.py15 import Cookie

_debug = 0


#############################################################################
### Form Handling
#############################################################################

_date_formats = {
    'iso':  '%Y-%m-%d %H:%M:%S',
    'us':   '%m/%d/%Y %I:%M:%S %p',
    'euro': '%d.%m.%Y %H:%M:%S',
    'rfc':  '%a %b %d %H:%M:%S %Y',
}

def savedata(pagename, request):
    """ Handle POST request of the user preferences form

        Return error msg or None
    """
    form = request.form

    if form.has_key('logout'):
        # clear the cookie in the browser and locally
        cookie = Cookie.Cookie(os.environ.get('HTTP_COOKIE', ''))
        if cookie.has_key('MOIN_ID'):
            uid = cookie['MOIN_ID'].value
            webapi.setHttpHeader(request, 'Set-Cookie: MOIN_ID=%s; expires=Tuesday, 01-Jan-1999 12:00:00 GMT; Path=%s' % (
                cookie['MOIN_ID'].value, webapi.getScriptname(),))
            os.environ['HTTP_COOKIE'] = ''
        request.user = user.User()
        user.current = request.user
        return _("<b>Cookie deleted!</b>")

    if form.has_key('login_sendmail'):
        import cgi

        try:
            email = form['login_email'].value
        except KeyError:
            return _("<b>Please provide a valid email address!</b>")

        text = ''
        users = user.getUserList()
        for uid in users:
            theuser = user.User(uid)
            if theuser.email == email:
                text = "%s\n\nID: %s\nName: %s\nLogin URL: %s?action=userform&uid=%s" % (
                    text, theuser.id, theuser.name, webapi.getBaseURL(), theuser.id)

        if not text:
            return _("<b>Found no account matching the given "
                "email address '%(email)s'!</b>") % {'email': email}

        msg = util.sendmail([email], 'Your wiki account data', text)
        return "<b>%s</b>" % cgi.escape(msg)

    if form.has_key('login') or form.has_key('uid'):
        # try to get the id
        try:
            uid = form['loginid'].value
        except KeyError:
            # check for "uid" value that we use in the relogin URL
            try:
                uid = form['uid'].value
            except KeyError:
                uid = None

        # if id is empty or missing, return an error msg
        if not uid:
            return _("<b>Please enter a non-empty user id!</b>")

        # load the user data and check for validness
        theuser = user.User(uid)
        if not theuser.valid:
            return _("<b>Please enter a valid user id!</b>")

        # send the cookie
        theuser.sendCookie(request)
        request.user = theuser
        user.current = theuser
    else:
        # save user's profile, first get user instance
        theuser = user.User()

        # try to get the name, if name is empty or missing, return an error msg
        try:
            theuser.name = string.replace(form['username'].value, '\t', ' ')
        except KeyError:
            return _("<b>Please enter a user name!</b>")

        # try to get the (optional) password
        try:
            theuser.password = form['password'].value
        except KeyError:
            theuser.password = ''

        # try to get the (optional) email
        try:
            theuser.email = form['email'].value
        except KeyError:
            theuser.email = ''

        # editor size
        try:
            theuser.edit_rows = int(form['edit_rows'].value)
            theuser.edit_rows = max(theuser.edit_rows, 10)
            theuser.edit_rows = min(theuser.edit_rows, 60)
        except KeyError:
            pass
        except ValueError:
            pass
        try:
            theuser.edit_cols = int(form['edit_cols'].value)
            theuser.edit_cols = max(theuser.edit_cols, 30)
            theuser.edit_cols = min(theuser.edit_cols, 100)
        except KeyError:
            pass
        except ValueError:
            pass

        # time zone
        try:
            theuser.tz_offset = int(form['tz_offset'].value)
        except KeyError:
            pass
        except ValueError:
            pass

        # date format
        try:
            theuser.datetime_fmt = _date_formats.get(form['datetime_fmt'].value, '')
        except KeyError:
            pass
        except ValueError:
            pass

        # CSS URL
        try:
            theuser.css_url = form['css_url'].value
        except KeyError:
            theuser.css_url = config.css_url
        except ValueError:
            pass
        if theuser.css_url == config.css_url:
            theuser.css_url = ''

        # try to get the (optional) preferred language
        theuser.language = form.getvalue('language', '')

        # checkbox options
        for key, label in user.User._checkbox_fields:
            value = form.getvalue(key, 0)
            try:
                value = int(value)
            except ValueError:
                pass
            else:
                setattr(theuser, key, value)

        # quicklinks for header
        try:
            quicklinks = form['quicklinks'].value
            quicklinks = string.replace(quicklinks, '\r', '')
            quicklinks = string.split(quicklinks, '\n')
            quicklinks = map(string.strip, quicklinks)
            quicklinks = filter(None, quicklinks)
            quicklinks = map(wikiutil.quoteWikiname, quicklinks)
            theuser.quicklinks = string.join(quicklinks, ',')
        except KeyError:
            theuser.quicklinks = ''
        except ValueError:
            pass
        
        # subscription for page change notification
        try:
            theuser.subscribed_pages = form['subscribed_pages'].value
            theuser.subscribed_pages = string.replace(theuser.subscribed_pages, '\r', '')
            theuser.subscribed_pages = string.replace(theuser.subscribed_pages, '\n', ',')
        except KeyError:
            theuser.subscribed_pages = ''
        except ValueError:
            pass
        
        # save data and send cookie
        theuser.save()
        theuser.sendCookie(request)
        request.user = theuser
        user.current = theuser

        result = _("<b>User preferences saved!</b>")
        if _debug:
            result = result + util.dumpFormData(form)
        return result


def _tz_select(theuser):
    html = '<select name="tz_offset">\n'

    tz = 0
    if theuser.valid: tz = int(theuser.tz_offset)

    now = time.time()
    for halfhour in range(-47, 48):
        offset = halfhour * 1800
        t = now + offset

        html = html + '<option value="%d"%s>%s [%s%s:%s]\n' % (
            offset,
            ('', ' selected')[offset == tz],
            time.strftime(config.datetime_fmt, time.localtime(t)),
            "+-"[offset < 0],
            string.zfill("%d" % (abs(offset) / 3600), 2),
            string.zfill("%d" % (abs(offset) % 3600 / 60), 2),
            )
    html = html + '</select>'

    return html


def _lang_select(theuser):
    cur_lang = theuser.valid and theuser.language or ''
    langs = languages.items()
    langs.append(('', ('&lt;Default&gt;', config.charset, '')))
    langs.sort(lambda x,y: cmp(x[1][0], y[1][0]))

    html = '<select name="language">\n'
    for lang in langs:
        # !!! If we add charset recoding, this restriction can be lifted
        if lang[0] in ['', 'en'] or lang[1][1] == config.charset:
            html = html + '<option value="%s"%s>%s\n' % (
                lang[0], lang[0] == cur_lang and ' selected' or '', lang[1][0])
    html = html + '</select>'
 
    return html
        

def getUserForm(request):
    form = request.form

    # Note that this form is NOT designed for security, just to have a cookie
    # with name & email; do not base security measures on this!
    htmlform = """
<form method="POST" action="%(scriptname)s%(pathinfo)s">
  <input type="hidden" name="action" value="userform">
  <table border="0">
    %(html_uid)s
    <tr><td><b>%(label_name)s</b>&nbsp;</td><td><input type="text" size="40" name="username" value="%(name)s"></td></tr>
    <tr><td><b>%(label_password)s</b>&nbsp;</td><td><input type="password" size="40" name="password" value="%(password)s"></td></tr>
    <tr><td><b>%(label_email)s</b>&nbsp;</td><td><input type="text" size="60" name="email" value="%(email)s"></td></tr>
    <tr><td><b>%(label_css_url)s</b>&nbsp;</td><td><input type="text" size="60" name="css_url" value="%(css_url)s"> %(label_css_help)s</td></tr>
    <tr><td><b>%(label_editor_size)s</b>&nbsp;</td><td>
      <input type="text" size="3" maxlength="3" name="edit_cols" value="%(edit_cols)s"> &nbsp;x&nbsp;
      <input type="text" size="3" maxlength="3" name="edit_rows" value="%(edit_rows)s">
    </td></tr>
    <tr><td><b>%(label_tz)s</b>&nbsp;</td><td>
      %(label_your_time)s %(tz_select)s  
      <br>%(label_server_time)s %(now)s
    </td></tr>
    <tr><td><b>%(label_date_format)s</b>&nbsp;</td><td>
      <select name="datetime_fmt">%(dtfmt_select)s</select>
    </td></tr>
    <tr><td><b>%(label_language)s</b>&nbsp;</td><td>
      %(language_select)s
    </td></tr>
    <tr><td><b>%(label_general_opts)s</b>&nbsp;</td><td>
      %(checkbox_fields)s
    </td></tr>
    <tr><td valign="top"><b>%(label_quicklinks)s</b>&nbsp;</td><td>
      <textarea name="quicklinks" rows="6" cols="50">%(quicklinklist)s</textarea>
    </td></tr>
    %(notify)s
    <tr><td></td><td>
      %(button)s
    </td></tr>
  </table>
</form>
%(relogin)s
"""
    formtext = {
        'label_name':           _('Name'),
        'label_password':       _('Password'),
        'label_email':          _('Email'),
        'label_css_url':        _('CSS URL'),
        'label_css_help':       _('("None" for disabling CSS)'),
        'label_editor_size':    _('Editor size'),
        'label_tz':             _('Time zone'),
        'label_your_time':      _('Your time is'),
        'label_server_time':    _('Server time is'),
        'label_date_format':    _('Date format'),
        'label_language':       _('Preferred language'),
        'label_quicklinks':     _('Quick links'),
        'label_general_opts':   _('General options'),
    }

    dtfmt_select = '<option value="">' + _('Default')
    for option, text in _date_formats.items():
        dtfmt_select = dtfmt_select + '<option value="%s"%s>%s' % (
            option, ('', ' selected')[request.user.datetime_fmt == text], text)

    if request.user.valid:
        html_uid = '<tr><td><b>ID</b>&nbsp;</td><td>%s</td></tr>' % (request.user.id,)
        html_button = """
            <input type="submit" name="save" value="%s"> &nbsp;
            <input type="submit" name="logout" value="%s"> &nbsp;
        """ % (_(' Save '), _(' Logout '))
        url = "%s?action=userform&uid=%s" % (webapi.getBaseURL(), request.user.id)
        html_relogin = _('To login on a different machine, use this URL: ') + \
            '<a href="%s">%s</a><br>' % (url, url)
    else:
        html_uid = """
            <tr><td><b>ID</b>&nbsp;</td><td><input type="text" size="40" name="loginid"></td></tr>
            <tr><td></td><td><input type="submit" name="login" value="%s"></td></tr>
        """ % (_(' Login '),)
        html_button = """
            <input type="submit" name="save" value="%s"> &nbsp;
        """ % (_(' Create Profile '),)
        html_relogin = ""

        if config.mail_smarthost:
            html_uid = """
                <tr><td><b>%s</b>&nbsp;</td><td><input type="text" size="40" name="login_email"></td></tr>
                <tr><td></td><td><input type="submit" name="login_sendmail" value="%s"></td></tr>%s
            """ % (_('Your email address'),
                   _(' Mail me my account data '),
                   html_uid)

    notify = ""
    if config.mail_smarthost:
        notifylist = request.user.getSubscriptionList()
        notifylist.sort()

        warning = ""
        if not request.user.email:
            warning = '<br/><font color="#FF4040"><small>' + \
                _("This list does not work, unless you have entered a valid email address!") + \
                '</small></font>'

        notify = """
<tr>
  <td valign="top"><b>%(label_notification)s</b>&nbsp;</td>
  <td><textarea name="subscribed_pages" rows="6" cols="50">%(notification)s</textarea>%(warning)s</td>
</tr>""" % {
            'label_notification': _('Subscribed wiki pages<br>(one regex per line)'),
            'notification': string.join(notifylist, '\n'),
            'warning': warning,
        }

    data = {
        'scriptname': webapi.getScriptname(),
        'pathinfo': webapi.getPathinfo(),
        'html_uid': html_uid,
        'button': html_button,
        'relogin': html_relogin,
        'now': time.strftime(config.datetime_fmt, time.localtime(time.time())),
        'tz_select': _tz_select(request.user),
        'dtfmt_select': dtfmt_select,
        'language_select': _lang_select(request.user),
        'notify': notify,
        'quicklinklist': string.join(request.user.getQuickLinks(), '\n'),
    }

    if not request.user.css_url:
        request.user.css_url = config.css_url

    data['checkbox_fields'] = ''
    checkbox_fields = user.User._checkbox_fields
    checkbox_fields.sort(lambda a, b: cmp(a[1](), b[1]()))
    for key, label in checkbox_fields:
        data['checkbox_fields'] = data['checkbox_fields'] + \
            '<input type="checkbox" name="%s" value="1"%s>&nbsp;%s<br>' % (
                key, ('', ' checked')[getattr(request.user, key, 0)], label())

    data.update(formtext)
    data.update(vars(request.user))
    result = htmlform % data

    return result

