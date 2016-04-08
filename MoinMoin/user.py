"""
    MoinMoin - User Accounts

    Copyright (c) 2000-2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: user.py,v 1.36 2001/07/16 21:45:22 jhermann Exp $
"""

# Imports
import os, string, time
from MoinMoin import config, i18n, webapi

try:
    import Cookie
except ImportError:
    from MoinMoin.py15 import Cookie


#############################################################################
### Helpers
#############################################################################

def getUserList():
    """ Get a list of all user IDs.
    """
    import re

    user_re = re.compile(r'^\d+\.\d+(\.\d+)?$')
    return filter(user_re.match, os.listdir(config.user_dir))


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

        # "may" so we can say "if user.may.edit:"
        if config.SecurityPolicy:
            self.may = config.SecurityPolicy(self)
        else:
            from security import Default
            self.may = Default(self)


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
            os.mkdir(config.user_dir, 0777 & config.umask)
            os.chmod(config.user_dir, 0777 & config.umask)

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
            os.chmod(self.__filename(), 0666 & config.umask)
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
                os.chmod(self.__filename() + ".bookmark", 0666 & config.umask)
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

