"""
    MoinMoin - User Account Maintenance

    Copyright (c) 2000-2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: userform.py,v 1.1 2001/07/16 21:45:22 jhermann Exp $
"""

# Imports
import os, string, time
from MoinMoin import config, user, util, webapi

try:
    import Cookie
except ImportError:
    from MoinMoin.py15 import Cookie


#############################################################################
### Form Handling
#############################################################################

_date_formats = {
    'iso':  '%Y-%m-%d %H:%M:%S',
    'us':   '%m/%d/%Y %I:%M:%S %p',
    'euro': '%d.%m.%Y %H:%M:%S',
    'rfc':  '%a %b %d %H:%M:%S %Y',
}

def savedata(pagename, form):
    """ Handle POST request of the user preferences form

        Return error msg or None
    """
    if form.has_key('logout'):
        # clear the cookie in the browser and locally
        cookie = Cookie.Cookie(os.environ.get('HTTP_COOKIE', ''))
        if cookie.has_key('MOIN_ID'):
            uid = cookie['MOIN_ID'].value
            webapi.setHttpHeader('Set-Cookie: MOIN_ID=%s; expires=Tuesday, 01-Jan-1999 12:00:00 GMT; Path=%s' % (
                cookie['MOIN_ID'].value, webapi.getScriptname(),))
            os.environ['HTTP_COOKIE'] = ''
        user.current = user.User()
        return user.current.text("<b>Cookie deleted!</b>")

    if form.has_key('login_sendmail'):
        import cgi

        try:
            email = form['login_email'].value
        except KeyError:
            return user.current.text("<b>Please provide a valid email address!</b>")

        text = ''
        users = user.getUserList()
        for uid in users:
            theuser = user.User(uid)
            if theuser.email == email:
                text = "%s\n\nID: %s\nName: %s\nLogin URL: %s?action=userform&uid=%s" % (
                    text, theuser.id, theuser.name, webapi.getBaseURL(), theuser.id)

        if not text:
            return user.current.text("<b>Found no account matching the given "
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
            return user.current.text("<b>Please enter a non-empty user id!</b>")

        # load the user data and check for validness
        theuser = user.User(uid)
        if not theuser.valid:
            return user.current.text("<b>Please enter a valid user id!</b>")

        # send the cookie
        theuser.sendCookie()
        user.current = theuser
    else:
        # save user's profile, first get user instance
        theuser = user.User()

        # try to get the name, if name is empty or missing, return an error msg
        try:
            theuser.name = string.replace(form['username'].value, '\t', ' ')
        except KeyError:
            return user.current.text("<b>Please enter a user name!</b>")

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

        # save data and send cookie
        theuser.save()
        theuser.sendCookie()
        user.current = theuser

        return user.current.text("<b>User preferences saved!</b>")


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


def getUserForm(form):
    # Note that this form is NOT designed for security, just to have a cookie
    # with name & email; do not base security measures on this!
    htmlform = """
<form method="POST" action="%(scriptname)s%(pathinfo)s">
  <input type="hidden" name="action" value="userform"></td></tr>
  <table border="0">
    %(html_uid)s
    <tr><td><b>%(label_name)s</b>&nbsp;</td><td><input type="text" size="40" name="username" value="%(name)s"></td></tr>
    <tr><td><b>%(label_password)s</b>&nbsp;</td><td><input type="password" size="40" name="password" value="%(password)s"></td></tr>
    <tr><td><b>%(label_email)s</b>&nbsp;</td><td><input type="text" size="40" name="email" value="%(email)s"></td></tr>
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
    <tr><td></td><td>
      %(button)s
    </td></tr>
  </table>
</form>
%(relogin)s
"""
    formtext = {
        'label_name':           user.current.text('Name'),
        'label_password':       user.current.text('Password'),
        'label_email':          user.current.text('Email'),
        'label_css_url':        user.current.text('CSS URL'),
        'label_css_help':       user.current.text('("None" for disabling CSS)'),
        'label_editor_size':    user.current.text('Editor size'),
        'label_tz':             user.current.text('Time zone'),
        'label_your_time':      user.current.text('Your time is'),
        'label_server_time':    user.current.text('Server time is'),
        'label_date_format':    user.current.text('Date format'),
    }

    dtfmt_select = '<option value="">' + user.current.text('Default')
    for option, text in _date_formats.items():
        dtfmt_select = dtfmt_select + '<option value="%s"%s>%s' % (
            option, ('', ' selected')[user.current.datetime_fmt == text], text)

    if user.current.valid:
        html_uid = '<tr><td><b>ID</b>&nbsp;</td><td>%s</td></tr>' % (user.current.id,)
        html_button = """
            <input type="submit" name="save" value="%s"> &nbsp;
            <input type="submit" name="logout" value="%s"> &nbsp;
        """ % (user.current.text(' Save '), user.current.text(' Logout '))
        url = "%s?action=userform&uid=%s" % (webapi.getBaseURL(), user.current.id)
        html_relogin = user.current.text('To login on a different machine, use this URL: ') + \
            '<a href="%s">%s</a><br>' % (url, url)
    else:
        html_uid = """
            <tr><td><b>ID</b>&nbsp;</td><td><input type="text" size="40" name="loginid"></td></tr>
            <tr><td></td><td><input type="submit" name="login" value="%s"></td></tr>
        """ % (user.current.text(' Login '),)
        html_button = """
            <input type="submit" name="save" value="%s"> &nbsp;
        """ % (user.current.text(' Create Profile '),)
        html_relogin = ""

        if config.mail_smarthost:
            html_uid = """
                <tr><td><b>%s</b>&nbsp;</td><td><input type="text" size="40" name="login_email"></td></tr>
                <tr><td></td><td><input type="submit" name="login_sendmail" value="%s"></td></tr>%s
            """ % (user.current.text('Your email address'),
                   user.current.text(' Mail me my account data '),
                   html_uid)

    data = {
        'scriptname': webapi.getScriptname(),
        'pathinfo': webapi.getPathinfo(),
        'html_uid': html_uid,
        'button': html_button,
        'relogin': html_relogin,
        'now': time.strftime(config.datetime_fmt, time.localtime(time.time())),
        'tz_select': _tz_select(user.current),
        'dtfmt_select': dtfmt_select,
    }
    data.update(formtext)
    data.update(vars(user.current))
    result = htmlform % data

    # from MoinMoin import cgimain
    # result = result + "Saved: <pre>" + cgimain.request.saved_cookie + "</pre>"
    # result = result + " Now: <pre>" + os.environ.get('HTTP_COOKIE', 'NONE') + "</pre>"

    return result

