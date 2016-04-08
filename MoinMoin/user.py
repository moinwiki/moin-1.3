# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - User Accounts

    @copyright: 2000-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

# Imports
import os, string, time, Cookie, sha, locale, pickle
from MoinMoin import config
from MoinMoin.util import datetime

#import sys

#############################################################################
### Helpers
#############################################################################

def getUserList():
    """
    Get a list of all (numerical) user IDs.
    
    @rtype: list
    @return: all user IDs
    """
    import re

    user_re = re.compile(r'^\d+\.\d+(\.\d+)?$')
    return filter(user_re.match, os.listdir(config.user_dir))

_name2id = None

def getUserId(searchName):
    """
    Get the user ID for a specific user NAME.

    @param searchName: the user name to look up
    @rtype: string
    @return: the corresponding user ID or None
    """
    global _name2id
    if not searchName:
        return None
    if not _name2id:
        userdictpickle = os.path.join(config.user_dir, "userdict.pickle")
        try:
            _name2id = pickle.load(open(userdictpickle))
        except (UnpicklingError,IOError,EOFError,ValueError):
            _name2id = {}
    id = _name2id.get(searchName, None)
    if id is None:
        for userid in getUserList():
            name = User(None, id=userid).name
            _name2id[name] = userid
        userdictpickle = os.path.join(config.user_dir, "userdict.pickle")
        pickle.dump(_name2id, open(userdictpickle,'w'))
        try:
            os.chmod(userdictpickle, 0666 & config.umask)
        except OSError:
            pass
        id = _name2id.get(searchName, None)
    return id

def getUserIdentification(request, username=None):
    """ 
    Return user name or IP or '<unknown>' indicator.
    
    @param request: the request object
    @param username: (optional) user name
    @rtype: string
    @return: user name or IP or unknown indicator
    """
    _ = request.getText

    if username is None:
        username = request.user.name

    return username or request.remote_addr or _("<unknown>")


def encodePassword(pwd):
    """
    Encode a cleartext password, compatible to Apache htpasswd SHA encoding.

    @param pwd: the cleartext password
    @rtype: string
    @return: the password in apache htpasswd compatible SHA-encoding
    """
    import base64
    return '{SHA}' + base64.encodestring(sha.new(pwd).digest()).rstrip()


#############################################################################
### User
#############################################################################

class User:
    """A MoinMoin User"""

    _checkbox_fields = [
         ('edit_on_doubleclick', lambda _: _('Open editor on double click')),
         ('remember_last_visit', lambda _: _('Remember last page visited')),
         ('show_emoticons', lambda _: _('Show emoticons')),
         ('show_fancy_links', lambda _: _('Show fancy links')),
         ('show_nonexist_qm', lambda _: _('Show question mark for non-existing pagelinks')),
         ('show_page_trail', lambda _: _('Show page trail')),
         ('show_toolbar', lambda _: _('Show icon toolbar')),
         ('show_topbottom', lambda _: _('Show top/bottom links in headings')),
         ('show_fancy_diff', lambda _: _('Show fancy diffs')),
         ('wikiname_add_spaces', lambda _: _('Add spaces to displayed wiki names')),
         ('remember_me', lambda _: _('Remember login information forever')),
         ('disabled', lambda _: _('Disable this account forever')),
    ]
    _transient_fields =  ['id', 'valid', 'may', 'auth_username', 'trusted']
    _MAX_TRAIL = config.trail_size

    def __init__(self, request, id=None, name="", password=None, auth_username=""):
        """
        Initialize user object
        
        @param request: the request object
        @param id: (optional) user ID
        @param name: (optional) user name
        @param password: (optional) user password
        @param auth_username: (optional) already authenticated user name (e.g. apache basic auth)
        """
        self.valid = 0
        self.id = id
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
        self.trusted = 0
        self.email = ""
        self.edit_rows = config.edit_rows
        self.edit_cols = 80
        self.tz_offset = int(float(config.tz_offset) * 3600)
        self.last_saved = str(time.time())
        self.css_url = ""
        self.language = ""
        self.quicklinks = ""
        self.datetime_fmt = ""
        self.subscribed_pages = ""
        self.theme_name = config.theme_default
        
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
                cookie = Cookie.SimpleCookie(request.saved_cookie)
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
        elif self.name:
            self.load()
        else:
            #!!! this should probably be a hash of REMOTE_ADDR, HTTP_USER_AGENT
            # and some other things identifying remote users, then we could also
            # use it reliably in edit locking
            from random import randint
            self.id = "%s.%d" % (str(time.time()), randint(0,65535))
            
        # "may" so we can say "if user.may.edit(pagename):"
        if config.SecurityPolicy:
            self.may = config.SecurityPolicy(self)
        else:
            from security import Default
            self.may = Default(self)


    def __filename(self):
        """
        get filename of the user's file on disk
        @rtype: string
        @return: full path and filename of user account file
        """
        return os.path.join(config.user_dir, self.id or "...NONE...")


    def exists(self):
        """
        Do we have a user account for this user?
        
        @rtype: bool
        @return: true, if we have a user account
        """
        return os.path.exists(self.__filename())


    def load(self):
        """
        Lookup user ID by user name and load user account.

        Can load user data if the user name is known, but only if the password is set correctly.
        """
        self.id = getUserId(self.name)
        if self.id:
            self.load_from_id(1)
        #print >>sys.stderr, "self.id: %s, self.name: %s" % (self.id, self.name)
        
    def load_from_id(self, check_pass=0):
        """
        Load user account data from disk.

        Can only load user data if the id number is already known.

        This loads all member variables, except "id" and "valid" and
        those starting with an underscore.
        
        @param check_pass: If 1, then self.enc_password must match the
                           password in the user account file.
        """
        if not self.exists(): return

        # XXX UNICODE fix needed, we want to read utf-8 and decode to unicode
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

        # convert (old) hourly format to seconds
        if -24 <= self.tz_offset and self.tz_offset <= 24:
            self.tz_offset = self.tz_offset * 3600

        # clear trail
        self._trail = []

        if not self.disabled:
            self.valid = 1


    def save(self):
        """
        Save user account data to user account file on disk.

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
        
        # XXX UNICODE fix needed, we want to write that file as utf-8
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


    def makeCookieHeader(self):
        """
        Make the Set-Cookie header for this user
            
        uses: config.cookie_lifetime (int) [hours]
            == 0  --> cookie will live forever (no matter what user has configured!)
            > 0   --> cookie will live for n hours (or forever when "remember_me")
            < 0   --> cookie will live for -n hours (forced, ignore "remember_me"!)
        """
        lifetime = int(config.cookie_lifetime) * 3600
        forever = 10*365*24*3600 # 10 years
        now = time.time()
        if not lifetime:
            expire = now + forever
        elif lifetime > 0:
            if self.remember_me:
                expire = now + forever
            else:
                expire = now + lifetime
        elif lifetime < 0:
            expire = now + (-lifetime)

        # XXX maybe better make this a critical section for persistent environments!?
        loc=locale.setlocale(locale.LC_TIME, 'C')
        expirestr = time.strftime("%A, %d-%b-%Y %H:%M:%S GMT", time.gmtime(expire))
        locale.setlocale(locale.LC_TIME, loc)

        cookie = Cookie.SimpleCookie()
        cookie['MOIN_ID'] = self.id
        return "%s expires=%s; Path=%s" % (cookie.output(), expirestr, self._request.getScriptname())


    def sendCookie(self, request):
        """
        Send the Set-Cookie header for this user.
        
        @param request: the request object
        """
        # prepare to send cookie
        request.setHttpHeader(self.makeCookieHeader())

        # create a "fake" cookie variable so the rest of the
        # code works as expected
        try:
            cookie = Cookie.SimpleCookie(request.saved_cookie)
        except Cookie.CookieError:
            # ignore invalid cookies, else user can't relogin
            request.saved_cookie = self.makeCookieHeader()
        else:
            if not cookie.has_key('MOIN_ID'):
                request.saved_cookie = self.makeCookieHeader()


    def getTime(self, tm):
        """
        Get time in user's timezone.
        
        @param tm: time (UTC UNIX timestamp)
        @rtype: int
        @return: tm tuple adjusted for user's timezone
        """
        return datetime.tmtuple(tm + self.tz_offset)


    def getFormattedDate(self, tm):
        """
        Get formatted date adjusted for user's timezone.

        @param tm: time (UTC UNIX timestamp)
        @rtype: string
        @return: formatted date, see config.date_fmt
        """
        return time.strftime(config.date_fmt, self.getTime(tm))


    def getFormattedDateTime(self, tm):
        """
        Get formatted date and time adjusted for user's timezone.

        @param tm: time (UTC UNIX timestamp)
        @rtype: string
        @return: formatted date and time, see config.datetime_fmt
        """
        datetime_fmt = self.datetime_fmt or config.datetime_fmt
        return time.strftime(datetime_fmt, self.getTime(tm))


    def setBookmark(self, tm = None):
        """
        Set bookmark timestamp.
        
        @param tm: time (UTC UNIX timestamp), default: current time
        """
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
        """
        Get bookmark timestamp.
        
        @rtype: int
        @return: bookmark time (UTC UNIX timestamp) or None
        """
        if self.valid and os.path.exists(self.__filename() + ".bookmark"):
            try:
                return int(open(self.__filename() + ".bookmark", 'r').readline())
            except (OSError, ValueError):
                return None
        return None


    def delBookmark(self):
        """
        Removes bookmark timestamp.

        @rtype: int
        @return: 0 on success, 1 on failure
        """
        if self.valid:
            if os.path.exists(self.__filename() + ".bookmark"):
                try:
                    os.unlink(self.__filename() + ".bookmark")
                except OSError:
                    return 1
            return 0
        return 1

    def getQuickLinks(self):
        """
        Get list of pages this user wants in the page header.

        @rtype: list
        @return: quicklinks from user account
        """
        if not self.quicklinks: return []

        from MoinMoin import wikiutil
        quicklinks = self.quicklinks.split(',')
        quicklinks = map(string.strip, quicklinks)
        quicklinks = filter(None, quicklinks)
        quicklinks = map(wikiutil.unquoteWikiname, quicklinks)
        return quicklinks


    def getSubscriptionList(self):
        """
        Get list of pages this user has subscribed to.
        
        @rtype: list
        @return: pages this user has subscribed to
        """
        subscrPages = self.subscribed_pages.split(",")
        subscrPages = map(string.strip, subscrPages)
        subscrPages = filter(None, subscrPages)
        return subscrPages


    def isSubscribedTo(self, pagelist):
        """
        Check if user subscription matches any page in pagelist.
        
        @param pagelist: list of pages to check for subscription
        @rtype: int
        @return: 1, if user has subscribed any page in pagelist
                 0, if not
        """
        import re

        matched = 0
        if self.valid:
            pagelist_lines = '\n'.join(pagelist)
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
        if matched:
            return 1
        else:
            return 0


    def subscribePage(self, pagename):
        """
        Subscribe to a wiki page.

        Note that you need to save the user data to make this stick!

        @param pagename: name of the page to subscribe
        @rtype: bool
        @return: true, if page was NEWLY subscribed.
        """
        subscrPages = self.getSubscriptionList()

        # add page to subscribed pages property
        if pagename not in subscrPages: 
            subscrPages.append(pagename)
            self.subscribed_pages = ','.join(subscrPages)
            return 1

        return 0


    def addTrail(self, pagename):
        """
        Add page to trail.
        
        @param pagename: the page name to add to the trail
        """
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
            # XXX UNICODE fix needed, encode as utf-8
            trailfile = open(self.__filename() + ".trail", "w")
            trailfile.write('\n'.join(self._trail))
            trailfile.close()
            try:
                os.chmod(self.__filename() + ".trail", 0666 & config.umask)
            except OSError:
                pass


    def getTrail(self):
        """
        Return list of recently visited pages.
        
        @rtype: list
        @return: pages in trail
        """
        if self.valid and (self.show_page_trail or self.remember_last_visit) \
                and not self._trail \
                and os.path.exists(self.__filename() + ".trail"):
            try:
                # XXX UNICODE fix needed, decode from utf-8
                self._trail = open(self.__filename() + ".trail", 'r').readlines()
            except (OSError, ValueError):
                self._trail = []
            else:
                self._trail = filter(None, map(string.strip, self._trail))
                self._trail = self._trail[-self._MAX_TRAIL:]
        return self._trail


