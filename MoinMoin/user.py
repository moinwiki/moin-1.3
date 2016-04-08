# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - User Accounts

    Copyright (c) 2000, 2001, 2002 by J�rgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: user.py,v 1.79 2003/11/22 21:15:28 thomaswaldmann Exp $
"""

# Imports
import os, string, time, Cookie, sha, locale, pickle
from MoinMoin import config, webapi
from MoinMoin.util import datetime
from MoinMoin.i18n import _

#import sys

#############################################################################
### Helpers
#############################################################################

def getUserList():
    """ Get a list of all user IDs.
    """
    import re

    user_re = re.compile(r'^\d+\.\d+(\.\d+)?$')
    return filter(user_re.match, os.listdir(config.user_dir))

_name2id = None

def getUserId(searchName):
    global _name2id
    if _name2id:
        id = _name2id.get(searchName, None)
    else:
        userdictpickle = os.path.join(config.user_dir, "userdict.pickle")
        try:
            _name2id = pickle.load(open(userdictpickle))
            id = _name2id[searchName]
        except (IOError, KeyError):
            _name2id = {}
            for userid in getUserList():
                name = User(None, id=userid).name
                _name2id[name] = userid
            pickle.dump(_name2id, open(userdictpickle,'w'))
            id = _name2id.get(searchName, None)
    return id

def getUserIdentification(request, username=None):
    """ Return user name or IP or '<unknown>' indicator.
    """
    _ = request.getText

    if username is None:
        username = request.user.name

    return username or os.environ.get('REMOTE_ADDR', _("<unknown>"))


def encodePassword(pwd):
    """ Encode a cleartext password, compatible to Apache htpasswd
        SHA encoding.
    """
    import base64
    return '{SHA}' + base64.encodestring(sha.new(pwd).digest()).rstrip()


#############################################################################
### User
#############################################################################

class User:
    """A MoinMoin User"""

    _checkbox_fields = [
        ('edit_on_doubleclick', lambda _=_: _('Open editor on double click')),
        ('remember_last_visit', lambda _=_: _('Remember last page visited')),
        ('show_emoticons', lambda _=_: _('Show emoticons')),
        ('show_fancy_links', lambda _=_: _('Show fancy links')),
        ('show_nonexist_qm', lambda _=_: _('Show question mark for non-existing pagelinks')),
        ('show_page_trail', lambda _=_: _('Show page trail')),
        ('show_toolbar', lambda _=_: _('Show icon toolbar')),
        ('show_topbottom', lambda _=_: _('Show top/bottom links in headings')),
        ('show_fancy_diff', lambda _=_: _('Show fancy diffs')),
        ('external_target', lambda _=_: _('Add "Open in new window" icon to pretty links')),
        ('wikiname_add_spaces', lambda _=_: _('Add spaces to displayed wiki names')),
        ('remember_me', lambda _=_: _('Remember login information forever')),
        ('disabled', lambda _=_: _('Disable this account forever')),
    ]
    _transient_fields =  ['id', 'valid', 'may', 'auth_username', 'trusted']
    _MAX_TRAIL = config.trail_size

    def __init__(self, request, id=None, name="", password=None, auth_username=""):
        """Init user with id"""
        self.valid      = 0
        self.id         = id
        if auth_username:
            self.auth_username = auth_username
        elif request:
            self.auth_username = request.auth_username
        else:
	    self.auth_username = ""
        self.name = name
        if not password:
            self.enc_password = ""
        else:
	    if password.startswith('{SHA}'):
                self.enc_password = password
            else:
	        self.enc_password = encodePassword(password)
        self.trusted    = 0
        self.email      = ""
        self.edit_rows  = config.edit_rows
        self.edit_cols  = 80
        self.tz_offset  = 0
        self.last_saved = str(time.time())
        self.css_url    = config.css_url
        self.language   = ""
        self.quicklinks = ""
        self.datetime_fmt = ""
        self.subscribed_pages = ""

        # if an account is disabled, it may be used for looking up
        # id -> username for page info and recent changes, but it
        # is not usabled for the user any more:
        # self.disabled   = 0
        # is handled by checkbox now.
	
        # attrs not saved to profile
        self._request = request
        self._trail = []

        # create checkbox fields (with default 0)
        for key, label in self._checkbox_fields:
            setattr(self, key, 0)
        self.show_page_trail = 1
        self.show_fancy_links = 1
        self.show_emoticons = 1
        self.show_toolbar = 1
        self.show_nonexist_qm = config.nonexist_qm
        self.show_fancy_diff = 1
        self.remember_me = 1

        if not self.id and not self.auth_username:
            try:
                cookie = Cookie.SimpleCookie(os.environ.get('HTTP_COOKIE', ''))
            except Cookie.CookieError:
                # ignore invalid cookies, else user can't relogin
                cookie = None
            if cookie and cookie.has_key('MOIN_ID'):
                self.id = cookie['MOIN_ID'].value

        # we got an already authenticated username:
        if not self.id and self.auth_username:
            self.id = getUserId(self.auth_username)

        if self.id:
            self.load_from_id()
	    if self.name == self.auth_username:
                self.trusted = 1
        else:
            #!!! this should probably be a hash of REMOTE_ADDR, HTTP_USER_AGENT
            # and some other things identifying remote users, then we could also
            # use it reliably in edit locking
            # CNC:2003-05-30
            self.id = str(time.time()) + "." + str(os.getpid())
            #from random import randint
            #self.id = hex(randint(0,1999999999))[2:]+hex(int(time.time()))[2:]+hex(os.getpid())[2:]

        if not self.valid and self.name:
            self.load()

        # "may" so we can say "if user.may.edit(pagename):"
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

            Can load user data if the user name is known, but only
            if the password is set correctly.
        """
        self.id = getUserId(self.name)
        if self.id:
            self.load_from_id(1)
        #print >>sys.stderr, "self.id: %s, self.name: %s" % (self.id, self.name)
	
    def load_from_id(self, check_pass=0):
        """ Load user data from disk

            Can only load user data if the id number is already known.

            This loads all member variables, except "id" and "valid" and
            those starting with an underscore.  If check_pass is set then
            self.enc_password must match the password in the file.
        """
        if not self.exists(): return

        data = open(self.__filename(), "r").readlines()
        user_data = {'enc_password': ''}
        for line in data:
            if line[0] == '#': continue

            try:
                key, val = line.strip().split('=', 1)
                if key not in self._transient_fields and key[0] != '_':
                    user_data[key] = val
            except ValueError:
                pass

	if check_pass:
            # If we have no password set, we don't accept login with username
	    if not user_data['enc_password']:
	        return
            # Check for a valid password
            elif user_data['enc_password'] != self.enc_password:
	        # print >>sys.stderr, "File:%s Form:%s" % (user_data['enc_password'], self.enc_password)
                return
	    else:
	        self.trusted = 1

        # Copy user data into user object
        for key, val in user_data.items():
            vars(self)[key] = val

        self.tz_offset = int(self.tz_offset)

        # old passwords are untrusted
        if hasattr(self, 'password'): del self.password
        if hasattr(self, 'passwd'): del self.passwd

        # make sure checkboxes are boolean
        for key, label in self._checkbox_fields:
            try:
                setattr(self, key, int(getattr(self, key)))
            except ValueError:
                setattr(self, key, 0)

        # convert (old) hourly format to minutes
        if -24 <= self.tz_offset and self.tz_offset <= 24:
            self.tz_offset = self.tz_offset * 3600

        # replace empty field by current default CSS
        if not self.css_url:
            self.css_url = config.css_url

        # clear trail
        self._trail = []

        if not self.disabled:
            self.valid = 1


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

        # !!! should write to a temp file here to avoid race conditions,
        # or even better, use locking
        data = open(self.__filename(), "w")
        data.write("# Data saved '%s' for id '%s'\n" % (
            time.strftime(config.datetime_fmt, time.localtime(time.time())),
            self.id))
        attrs = vars(self).items()
        attrs.sort()
        for key, value in attrs:
            if key not in self._transient_fields and key[0] != '_':
                data.write("%s=%s\n" % (key, str(value)))
        data.close()

        try:
            os.chmod(self.__filename(), 0666 & config.umask)
        except OSError:
            pass

        if not self.disabled:
            self.valid = 1


    def getCookie(self):
        """Get the Set-Cookie header for this user"""
        cookie = Cookie.SimpleCookie()
        cookie['MOIN_ID'] = self.id
        if self.remember_me:
            ret=cookie.output() + ' expires=Tuesday, 31-Dec-2013 12:00:00 GMT; Path=%s' % (webapi.getScriptname(),)
        else:
            loc=locale.setlocale(locale.LC_TIME, 'C')
            ret=cookie.output() + ' expires='+time.strftime("%A, %d-%b-%Y 23:59:59 GMT")+'; Path=%s' % (webapi.getScriptname(),)
            locale.setlocale(locale.LC_TIME, loc)
        return ret


    def sendCookie(self, request):
        """Send the Set-Cookie header for this user"""
        # prepare to send cookie
        webapi.setHttpHeader(request, self.getCookie())

        # create a "fake" cookie variable so the rest of the
        # code works as expected
        try:
            cookie = Cookie.SimpleCookie(os.environ.get('HTTP_COOKIE', ''))
        except Cookie.CookieError:
            # ignore invalid cookies, else user can't relogin
            os.environ['HTTP_COOKIE'] = self.getCookie()
        else:
            if not cookie.has_key('MOIN_ID'):
                os.environ['HTTP_COOKIE'] = self.getCookie()


    def getTime(self, tm):
        """Get time in user's timezone"""
        return datetime.tmtuple(tm + self.tz_offset)


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
                return int(open(self.__filename() + ".bookmark", 'r').readline())
            except (OSError, ValueError):
                return None
        return None


    def getQuickLinks(self):
        """ Get list of pages this user wants in the page header.
        """
        if not self.quicklinks: return []

        from MoinMoin import wikiutil
        quicklinks = self.quicklinks.split(',')
        quicklinks = map(string.strip, quicklinks)
        quicklinks = filter(None, quicklinks)
        quicklinks = map(wikiutil.unquoteWikiname, quicklinks)
        return quicklinks


    def getSubscriptionList(self):
        """ Get list of pages this user has subscribed to.
        """
        subscrPages = self.subscribed_pages.split(",")
        subscrPages = map(string.strip, subscrPages)
        subscrPages = filter(None, subscrPages)
        return subscrPages


    def isSubscribedTo(self, pagelist):
        """ Return TRUE if user subscription matches any page in pagelist.
        """
        import re

        pagelist_lines = '\n'.join(pagelist)
        matched = 0
        for pattern in self.getSubscriptionList():
            # check if pattern matches one of the pages in pagelist
            matched = pattern in pagelist
            if matched: break
            try:
                rexp = re.compile("^"+pattern+"$", re.M)
            except re.error:
                # skip bad regex
                continue
            matched = rexp.search(pagelist_lines)
            if matched: break

        return matched


    def subscribePage(self, pagename):
        """ Subscribe to a wiki page, return TRUE if it was newly subscribed.

            Note that you need to save the user data to make this stick!
        """
        subscrPages = self.getSubscriptionList()

        # add page to subscribed pages property
        if pagename not in subscrPages: 
            subscrPages.append(pagename)
            self.subscribed_pages = ','.join(subscrPages)
            return 1

        return 0


    def addTrail(self, pagename):
        """Add page to trail"""
        if self.valid and (self.show_page_trail or self.remember_last_visit):
            # load trail if not known
            self.getTrail()      
            
            # don't append tail to trail ;)
            if self._trail and self._trail[-1] == pagename: return

            # append new page, limiting the length
            self._trail = filter(lambda p, pn=pagename: p != pn, self._trail)
            self._trail = self._trail[-(self._MAX_TRAIL-1):]
            self._trail.append(pagename)

            # save new trail
            trailfile = open(self.__filename() + ".trail", "w")
            trailfile.write('\n'.join(self._trail))
            trailfile.close()
            try:
                os.chmod(self.__filename() + ".trail", 0666 & config.umask)
            except OSError:
                pass


    def getTrail(self):
        """Return list of recently visited pages"""
        if self.valid and (self.show_page_trail or self.remember_last_visit) \
                and not self._trail \
                and os.path.exists(self.__filename() + ".trail"):
            try:
                self._trail = open(self.__filename() + ".trail", 'r').readlines()
            except (OSError, ValueError):
                self._trail = []
            else:
                self._trail = filter(None, map(string.strip, self._trail))
                self._trail = self._trail[-self._MAX_TRAIL:]
        return self._trail


