"""
    MoinMoin - User Accounts

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: user.py,v 1.18 2000/12/07 23:18:21 jhermann Exp $
"""

# Imports
import os, string, time
from MoinMoin import config, util

try:
    import Cookie
except ImportError:
    from MoinMoin.py15 import Cookie


#############################################################################
### Form Handling
#############################################################################

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
            util.setHttpHeader('Set-Cookie: MOIN_ID=%s; expires=Tuesday, 01-Jan-1999 12:00:00 GMT; Path=%s' % (
                cookie['MOIN_ID'].value, util.getScriptname(),))
            os.environ['HTTP_COOKIE'] = ''
        current = User()
        return "<b>Cookie deleted!</b>"

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
            return "<b>Please enter a non-empty user id!</b>"

        # load the user data and check for validness
        user = User(uid)
        if not user.valid:
            return "<b>Please enter a valid user id!</b>"

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
            return "<b>Please enter a user name!</b>"

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

        # save data and send cookie
        user.save()
        user.sendCookie()
        current = user

        return "<b>User preferences saved!</b>"


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
    <tr><td><b>Name</b>&nbsp;</td><td><input type="text" size="40" name="username" value="%(name)s"></td></tr>
    <tr><td><b>Password</b>&nbsp;</td><td><input type="password" size="40" name="password" value="%(password)s"></td></tr>
    <tr><td><b>Email</b>&nbsp;</td><td><input type="text" size="40" name="email" value="%(email)s"></td></tr>
    <tr><td><b>Editor size</b>&nbsp;</td><td>
      <input type="text" size="3" maxlength="3" name="edit_cols" value="%(edit_cols)s"> &nbsp;x&nbsp;
      <input type="text" size="3" maxlength="3" name="edit_rows" value="%(edit_rows)s">
    </td></tr>
    <tr><td><b>Time zone</b>&nbsp;</td><td>
      Your time is %(tz_select)s  
      <br>Server time is %(now)s
    </td></tr>
    <tr><td></td><td>
      %(button)s
    </td></tr>
  </table>
</form>
%(relogin)s
"""

    if current.valid:
        html_uid = '<tr><td><b>ID</b>&nbsp;</td><td>%s</td></tr>' % (current.id,)
        html_button = """
            <input type="submit" name="save" value=" Save "> &nbsp;
            <input type="submit" name="logout" value=" Logout "> &nbsp;
        """
        url = "http://%s:%s%s?action=userform&uid=%s" % (
            os.environ.get('SERVER_NAME'), os.environ.get('SERVER_PORT'),
            util.getScriptname(), current.id)
        html_relogin = 'To login on a different machine, use this URL: ' + \
            '<a href="%s">%s</a><br>' % (url, url)
    else:
        html_uid = """
            <tr><td><b>ID</b>&nbsp;</td><td><input type="text" size="40" name="loginid"></td></tr>
            <tr><td></td><td><input type="submit" name="login" value=" Login "></td></tr>
        """
        html_button = """
            <input type="submit" name="save" value=" Create Profile "> &nbsp;
        """
        html_relogin = ""

    data = {
        'scriptname': util.getScriptname(),
        'pathinfo': util.getPathinfo(),
        'html_uid': html_uid,
        'button': html_button,
        'relogin': html_relogin,
        'now': time.strftime(config.datetime_fmt, time.localtime(time.time())),
        'tz_select': _tz_select(current),
    }
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
        """Load user data from disk"""
        if not self.exists(): return

        data = open(self.__filename(), "rt").readlines()
        for line in data:
            if line[0] == '#': continue

            try:
                key, val = string.split(string.strip(line), '=', 1)
                if key not in ['id', 'valid']:
                    vars(self)[key] = val
            except ValueError:
                pass

        self.valid = 1
        self.tz_offset = int(self.tz_offset)

        # convert (old) hourly format to minutes
        if -24 <= self.tz_offset and self.tz_offset <= 24:
            self.tz_offset = self.tz_offset * 3600        


    def save(self):
        """Save user data to disk"""
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
            if key not in ['id', 'valid']:
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
        return cookie.output() + ' expires=Tuesday, 31-Dec-2013 12:00:00 GMT; Path=%s' % (util.getScriptname(),)


    def sendCookie(self):
        """Send the Set-Cookie header for this user"""
        # prepare to send cookie
        util.setHttpHeader(self.getCookie())

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
        #datetime_fmt = '%Y-%m-%d %H:%M:%S'
        return time.strftime(config.datetime_fmt, self.getTime(tm))


    def setBookmark(self, tm = None):
        """Set bookmark timestamp"""
        if self.valid:
            if not tm: tm = time.time()
            open(self.__filename() + ".bookmark", "w").write(str(tm)+"\n")
            try:
                os.utime(self.__filename() + ".bookmark", (tm, tm))
                os.chmod(self.__filename() + ".bookmark", 0666)
            except OSError:
                pass


    def getBookmark(self):
        """Return None or saved bookmark timestamp"""
        if self.valid and os.path.exists(self.__filename() + ".bookmark"):
            return os.path.getmtime(self.__filename() + ".bookmark")
        return None


# current user
current = User()

