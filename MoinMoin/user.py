"""
    MoinMoin - User Accounts

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: user.py,v 1.30 2001/05/04 21:32:39 jhermann Exp $
"""

# Imports
import os, string, time
from MoinMoin import config, i18n, util, webapi

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
    global current

    if form.has_key('logout'):
        # clear the cookie in the browser and locally
        cookie = Cookie.Cookie(os.environ.get('HTTP_COOKIE', ''))
        if cookie.has_key('MOIN_ID'):
            uid = cookie['MOIN_ID'].value
            webapi.setHttpHeader('Set-Cookie: MOIN_ID=%s; expires=Tuesday, 01-Jan-1999 12:00:00 GMT; Path=%s' % (
                cookie['MOIN_ID'].value, webapi.getScriptname(),))
            os.environ['HTTP_COOKIE'] = ''
        current = User()
        return current.text("<b>Cookie deleted!</b>")

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
            return current.text("<b>Please enter a non-empty user id!</b>")

        # load the user data and check for validness
        user = User(uid)
        if not user.valid:
            return current.text("<b>Please enter a valid user id!</b>")

        # send the cookie
        user.sendCookie()
        current = user
    else:
        # save user's profile, first get user instance
        user = User()

        # try to get the name, if name is empty or missing, return an error msg
        try:
            user.name = string.replace(form['username'].value, '\t', ' ')
        except KeyError:
            return current.text("<b>Please enter a user name!</b>")

        # try to get the (optional) password
        try:
            user.password = form['password'].value
        except KeyError:
            user.password = ''
    
        # try to get the (optional) email
        try:
            user.email = form['email'].value
        except KeyError:
            user.email = ''

        # editor size
        try:
            user.edit_rows = int(form['edit_rows'].value)
            user.edit_rows = max(user.edit_rows, 10)
            user.edit_rows = min(user.edit_rows, 60)
        except KeyError:
            pass
        except ValueError:
            pass
        try:
            user.edit_cols = int(form['edit_cols'].value)
            user.edit_cols = max(user.edit_cols, 30)
            user.edit_cols = min(user.edit_cols, 100)
        except KeyError:
            pass
        except ValueError:
            pass

        # time zone
        try:
            user.tz_offset = int(form['tz_offset'].value)
        except KeyError:
            pass
        except ValueError:
            pass

        # date format
        try:
            user.datetime_fmt = _date_formats.get(form['datetime_fmt'].value, '')
        except KeyError:
            pass
        except ValueError:
            pass

        # CSS URL
        try:
            user.css_url = form['css_url'].value
        except KeyError:
            user.css_url = config.css_url
        except ValueError:
            pass

        # save data and send cookie
        user.save()
        user.sendCookie()
        current = user

        return current.text("<b>User preferences saved!</b>")


def _tz_select(user):
    html = '<select name="tz_offset">\n'

    tz = 0
    if user.valid: tz = int(user.tz_offset)

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
        'label_name':           current.text('Name'),
        'label_password':       current.text('Password'),
        'label_email':          current.text('Email'),
        'label_css_url':        current.text('CSS URL'),
        'label_css_help':       current.text('("None" for disabling CSS)'),
        'label_editor_size':    current.text('Editor size'),
        'label_tz':             current.text('Time zone'),
        'label_your_time':      current.text('Your time is'),
        'label_server_time':    current.text('Server time is'),
        'label_date_format':    current.text('Date format'),
    }

    dtfmt_select = '<option value="">' + current.text('Default')
    for option, text in _date_formats.items():
        dtfmt_select = dtfmt_select + '<option value="%s"%s>%s' % (
            option, ('', ' selected')[current.datetime_fmt == text], text)

    if current.valid:
        html_uid = '<tr><td><b>ID</b>&nbsp;</td><td>%s</td></tr>' % (current.id,)
        html_button = """
            <input type="submit" name="save" value="%s"> &nbsp;
            <input type="submit" name="logout" value="%s"> &nbsp;
        """ % (current.text(' Save '), current.text(' Logout '))
        url = "%s?action=userform&uid=%s" % (webapi.getBaseURL(), current.id)
        html_relogin = current.text('To login on a different machine, use this URL: ') + \
            '<a href="%s">%s</a><br>' % (url, url)
    else:
        html_uid = """
            <tr><td><b>ID</b>&nbsp;</td><td><input type="text" size="40" name="loginid"></td></tr>
            <tr><td></td><td><input type="submit" name="login" value="%s"></td></tr>
        """ % (current.text(' Login '),)
        html_button = """
            <input type="submit" name="save" value="%s"> &nbsp;
        """ % (current.text(' Create Profile '),)
        html_relogin = ""

    data = {
        'scriptname': webapi.getScriptname(),
        'pathinfo': webapi.getPathinfo(),
        'html_uid': html_uid,
        'button': html_button,
        'relogin': html_relogin,
        'now': time.strftime(config.datetime_fmt, time.localtime(time.time())),
        'tz_select': _tz_select(current),
        'dtfmt_select': dtfmt_select,
    }
    data.update(formtext)
    data.update(vars(current))
    result = htmlform % data

    # import cgimain
    # result = result + "Saved: <pre>" + cgimain.saved_cookie + "</pre>"
    # result = result + " Now: <pre>" + os.environ.get('HTTP_COOKIE', 'NONE') + "</pre>"

    return result


#############################################################################
### User
#############################################################################

class User:
    """A MoinMoin User"""

    def __init__(self, id=None):
        """Init user with id"""
        self.valid      = 0
        self.id         = id
        self.name       = ""
        self.password   = ""
        self.email      = ""
        self.edit_rows  = config.edit_rows
        self.edit_cols  = 80
        self.tz_offset  = 0
        self.last_saved = str(time.time())
        self.datetime_fmt = ""
        self.css_url    = config.css_url
        self._i18ntext  = None

        if not self.id:
            cookie = Cookie.Cookie(os.environ.get('HTTP_COOKIE', ''))
            if cookie.has_key('MOIN_ID'):
                self.id = cookie['MOIN_ID'].value

        if self.id:
            self.load()
        else:
            self.id = str(time.time()) + "." + str(os.getpid())


    def __filename(self):
        """Name of the user's file on disk"""
        return os.path.join(config.user_dir, self.id or "...NONE...")


    def exists(self):
        """Do we have data stored for this user?"""
        return os.path.exists(self.__filename())


    def load(self):
        """ Load user data from disk

            This loads all member variables, except "id" and "valid" and
            those starting with an underscore.
        """
        if not self.exists(): return

        data = open(self.__filename(), "rt").readlines()
        for line in data:
            if line[0] == '#': continue

            try:
                key, val = string.split(string.strip(line), '=', 1)
                if key not in ['id', 'valid'] and key[0] != '_':
                    vars(self)[key] = val
            except ValueError:
                pass

        self.valid = 1
        self.tz_offset = int(self.tz_offset)

        # convert (old) hourly format to minutes
        if -24 <= self.tz_offset and self.tz_offset <= 24:
            self.tz_offset = self.tz_offset * 3600        


    def save(self):
        """ Save user data to disk

            This saves all member variables, except "id" and "valid" and
            those starting with an underscore.
        """
        if not self.id: return

        if not os.path.isdir(config.user_dir):
            os.mkdir(config.user_dir, 0777)
            os.chmod(config.user_dir, 0777)

        self.last_saved = str(time.time())

        data = open(self.__filename(), "wt")
        data.write("# Data saved '%s' for id '%s'\n" % (
            time.strftime(config.datetime_fmt, time.localtime(time.time())),
            self.id))
        for key, value in vars(self).items():
            if key not in ['id', 'valid'] and key[0] != '_':
                data.write("%s=%s\n" % (key, str(value)))
        data.close()

        try:
            os.chmod(self.__filename(), 0666)
        except OSError:
            pass

        self.valid = 1


    def getCookie(self):
        """Get the Set-Cookie header for this user"""
        cookie = Cookie.SimpleCookie()
        cookie['MOIN_ID'] = self.id
        return cookie.output() + ' expires=Tuesday, 31-Dec-2013 12:00:00 GMT; Path=%s' % (webapi.getScriptname(),)


    def sendCookie(self):
        """Send the Set-Cookie header for this user"""
        # prepare to send cookie
        webapi.setHttpHeader(self.getCookie())

        # create a "fake" cookie variable so the rest of the
        # code works as expected
        cookie = Cookie.Cookie(os.environ.get('HTTP_COOKIE', ''))
        if not cookie.has_key('MOIN_ID'):
            os.environ['HTTP_COOKIE'] = self.getCookie()


    def getTime(self, tm):
        """Get time in user's timezone"""
        return time.localtime(tm + self.tz_offset)


    def getFormattedDate(self, tm):
        #date_fmt = '%Y-%m-%d'
        return time.strftime(config.date_fmt, self.getTime(tm))


    def getFormattedDateTime(self, tm):
        datetime_fmt = self.datetime_fmt or config.datetime_fmt
        return time.strftime(datetime_fmt, self.getTime(tm))


    def setBookmark(self, tm = None):
        """Set bookmark timestamp"""
        if self.valid:
            if not tm: tm = time.time()
            bmfile = open(self.__filename() + ".bookmark", "w")
            bmfile.write(str(tm)+"\n")
            bmfile.close()
            try:
                os.chmod(self.__filename() + ".bookmark", 0666)
            except OSError:
                pass
            try:
                os.utime(self.__filename() + ".bookmark", (tm, tm))
            except OSError:
                pass


    def getBookmark(self):
        """Return None or saved bookmark timestamp"""
        if self.valid and os.path.exists(self.__filename() + ".bookmark"):
            try:
                return int(open(self.__filename() + ".bookmark", 'rt').readline())
            except (OSError, ValueError):
                return None
        return None


    def getLang(self):
        """Get a user's language"""
        accepted = os.environ.get('HTTP_ACCEPT_LANGUAGE')
        if accepted:
            accepted = string.split(accepted, ',')
            accepted = map(lambda x: string.split(x, '-')[0], accepted)
            accepted = map(lambda x: string.split(x, ';')[0], accepted)

            for lang in accepted:
                if i18n.languages.has_key(lang):
                    return lang

        return 'en'


    def text(self, str):
        """Load a text in the user's language"""
        # quick handling for english texts
        lang = self.getLang()
        if lang == "en": return str

        # load texts if needed
        if not self._i18ntext:
            self._i18ntext = i18n.loadLanguage(lang)
            if not self._i18ntext:
                return str

        # check for text additions, if configured (only active in development setups)
        if config.check_i18n and not self._i18ntext.has_key(str):
            self._i18ntext[str] = str
            i18n.saveLanguage(lang, self._i18ntext)

        # return the matching entry in the mapping table
        return self._i18ntext.get(str, str)


# current user
current = User()

