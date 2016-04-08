# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - User Account Maintenance

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: userform.py,v 1.54 2003/11/09 21:00:51 thomaswaldmann Exp $
"""

# Imports
import os, string, time, cgi, re, sha, Cookie
from MoinMoin import config, user, util, webapi, wikiutil
import MoinMoin.util.web
import MoinMoin.util.mail
import MoinMoin.util.datetime
from MoinMoin.widget import html

_debug = 0


#############################################################################
### Form POST Handling
#############################################################################

def savedata(pagename, request):
    """ Handle POST request of the user preferences form.

        Return error msg or None.
    """
    return UserSettingsHandler(request).handleData()


class UserSettingsHandler:

    def __init__(self, request):
        """ Initialize user settings form.
        """
        self.request = request
        self._ = request.getText


    def handleData(self):
        _ = self._
        form = self.request.form
    
        if form.has_key('logout'):
            # clear the cookie in the browser and locally
            try:
                cookie = Cookie.SimpleCookie(os.environ.get('HTTP_COOKIE', ''))
            except Cookie.CookieError:
                # ignore invalid cookies
                cookie = None
            else:
                if cookie.has_key('MOIN_ID'):
                    uid = cookie['MOIN_ID'].value
                    webapi.setHttpHeader(self.request, 'Set-Cookie: MOIN_ID=%s; expires=Tuesday, 01-Jan-1999 12:00:00 GMT; Path=%s' % (
                        cookie['MOIN_ID'].value, webapi.getScriptname(),))
            os.environ['HTTP_COOKIE'] = ''
            self.request.auth_username = ''
            self.request.user = user.User(self.request)
            user.current = self.request.user
            return _("<b>Cookie deleted. You are now logged out.</b>")
    
        if form.has_key('login_sendmail'):
            try:
                email = form['login_email'].value
            except KeyError:
                return _("<b>Please provide a valid email address!</b>")
    
            text = ''
            users = user.getUserList()
            for uid in users:
                theuser = user.User(self.request, uid)
                if theuser.valid and theuser.email == email:
                    text = "%s\n\nID: %s\nName: %s\nPassword: %s\nLogin URL: %s?action=userform&uid=%s" % (
                        text, theuser.id, theuser.name, theuser.enc_password, webapi.getBaseURL(), theuser.id)
   
            if not text:
                return _("<b>Found no account matching the given "
                    "email address '%(email)s'!</b>") % {'email': email}
    
            mailok, msg = util.mail.sendmail(self.request, [email], 
                'Your wiki account data', text, mail_from=email)
            return "<b>%s</b>" % cgi.escape(msg)
    
        if form.has_key('login') or form.has_key('uid'):
            # check for "uid" value that we use in the relogin URL
            try:
                 uid = form['uid'].value
            except KeyError:
                 uid = None

            # try to get the user name
            try:
                name = form['username'].value.replace('\t', ' ').strip()
            except KeyError:
                name = ''

            # try to get the password
            password = form.getvalue('password','')
  
            # load the user data and check for validness
            theuser = user.User(self.request, uid, name=name, password=password)
            if not theuser.valid:
                return _("<b>Unknown user name or password.</b>")

            # send the cookie
            theuser.sendCookie(self.request)
            self.request.user = theuser
            user.current = theuser
        else:
            # save user's profile, first get user instance
            theuser = user.User(self.request)
    
            # try to get the name, if name is empty or missing, return an error msg
            try:
                theuser.name = form['username'].value.replace('\t', ' ').strip()
            except KeyError:
                return _("<b>Please enter a user name!</b>")
    
            # Is this an existing user trying to change password, or a new user?
            newuser = 1
            if user.getUserId(theuser.name):
	        if theuser.name != user.current.name:
                    return _("<b>User name already exists!</b>")
                else:
                    newuser = 0

            # try to get the (optional) password and pw repeat
            password = form.getvalue('password', '')
            password2 = form.getvalue('password2','')

            # Check if password and password repeat match
            if password != password2:
                return _("<b>Passwords don't match!</b>")
            elif password and not password.startswith('{SHA}'):
                theuser.enc_password = user.encodePassword(password)

            # try to get the (optional) email
            theuser.email = form.getvalue('email', '')
    
            # editor size
            theuser.edit_rows = util.web.getIntegerInput(self.request, 'edit_rows', theuser.edit_rows, 10, 60)
            theuser.edit_cols = util.web.getIntegerInput(self.request, 'edit_cols', theuser.edit_cols, 30, 100)
    
            # time zone
            theuser.tz_offset = util.web.getIntegerInput(self.request, 'tz_offset', theuser.tz_offset, -84600, 84600)
    
            # date format
            try:
                theuser.datetime_fmt = UserSettings._date_formats.get(form['datetime_fmt'].value, '')
            except (KeyError, ValueError):
                pass
    
            # CSS URL
            theuser.css_url = form.getvalue('css_url', '')
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
            quicklinks = form.getvalue('quicklinks', '')
            quicklinks = quicklinks.replace('\r', '')
            quicklinks = quicklinks.split('\n')
            quicklinks = map(string.strip, quicklinks)
            quicklinks = filter(None, quicklinks)
            quicklinks = map(wikiutil.quoteWikiname, quicklinks)
            theuser.quicklinks = ','.join(quicklinks)
            
            # subscription for page change notification
            theuser.subscribed_pages = form.getvalue('subscribed_pages', '')
            theuser.subscribed_pages = theuser.subscribed_pages.replace('\r', '')
            theuser.subscribed_pages = theuser.subscribed_pages.replace('\n', ',')
            
            # if we use ACLs, name and email are required to be unique
            # further, name is required to be a WikiName (CamelCase!)
            # see also MoinMoin/scripts/moin_usercheck.py
            if config.acl_enabled:
                theuser.name = theuser.name.replace(' ','') # strip spaces, we don't allow them anyway
                if not re.match("(?:[%(u)s][%(l)s]+){2,}" % {'u': config.upperletters, 'l': config.lowerletters}, theuser.name):
                    return _("<b>Please enter your name like that: FirstnameLastname</b>")
                if not theuser.email or not re.match(".+@.+\..{2,}", theuser.email):
		    return _("<b>Please provide your email address - without that you could not get your login data via email just in case you lose it.</b>")
                users = user.getUserList()
                for uid in users:
                    if uid == theuser.id:
                        continue
                    thisuser = user.User(self.request, uid)
                    if thisuser.name == theuser.name:
                        return _("<b>This user name already belongs to somebody else.</b>")
                    if theuser.email and thisuser.email == theuser.email:
                        return _("<b>This email already belongs to somebody else.</b>")


            # save data and send cookie
            theuser.save()
            theuser.sendCookie(self.request)
            self.request.user = theuser
            user.current = theuser
    
            result = _("<b>User preferences saved!</b>")
            if _debug:
                result = result + util.dumpFormData(form)
            return result


#############################################################################
### Form Generation
#############################################################################

class UserSettings:
    """ User login and settings management.
    """

    _date_formats = {
        'iso':  '%Y-%m-%d %H:%M:%S',
        'us':   '%m/%d/%Y %I:%M:%S %p',
        'euro': '%d.%m.%Y %H:%M:%S',
        'rfc':  '%a %b %d %H:%M:%S %Y',
    }


    def __init__(self, request):
        """ Initialize user settings form.
        """
        self.request = request
        self._ = request.getText


    def _tz_select(self):
        """ Create time zone selection.
        """
        tz = 0
        if self.request.user.valid:
            tz = int(self.request.user.tz_offset)

        options = []
        now = time.time()
        for halfhour in range(-47, 48):
            offset = halfhour * 1800
            t = now + offset

            options.append((
                offset,
                '%s [%s%s:%s]' % (
                    time.strftime(config.datetime_fmt, util.datetime.tmtuple(t)),
                    "+-"[offset < 0],
                    string.zfill("%d" % (abs(offset) / 3600), 2),
                    string.zfill("%d" % (abs(offset) % 3600 / 60), 2),
                ),
            ))
 
        return util.web.makeSelection('tz_offset', options, tz)


    def _dtfmt_select(self):
        """ Create date format selection.
        """
        try:
            selected = [
                k for k, v in self._date_formats.items()
                    if v == self.request.user.datetime_fmt][0]
        except IndexError:
            selected = ''
        options = [('', self._('Default'))] + self._date_formats.items()

        return util.web.makeSelection('datetime_fmt', options, selected)


    def _lang_select(self):
        """ Create language selection.
        """
        from MoinMoin.i18n import languages, NAME, ENCODING

        cur_lang = self.request.user.valid and self.request.user.language or ''
        langs = languages.items()
        langs.sort(lambda x,y,NAME=NAME: cmp(x[1][NAME], y[1][NAME]))

        options = [('', self._('<Browser setting>'))]
        for lang in langs:
            if config.charset.upper() == 'UTF-8' or \
                    lang[0] in ['', 'en'] or \
                    lang[1][ENCODING] == config.charset:
                options.append((lang[0], lang[1][NAME]))
 
        return util.web.makeSelection('language', options, cur_lang)


    def make_form(self):
        """ Create the FORM, and the TABLE with the input fields
        """
        self._form = html.FORM(action=webapi.getScriptname()+webapi.getPathinfo())
        self._table = html.TABLE(border=0)

        self._form.append(html.INPUT(type="hidden", name="action", value="userform"))
        self._form.append(self._table)


    def make_row(self, label, cell, **kw):
        """ Create a row in the form table.
        """
        self._table.append(html.TR().extend([
            html.TD(**kw).extend([html.B().append(label), '\xA0']),
            html.TD().extend(cell),
        ]))


    def asHTML(self):
        """ Create the complete HTML form code.
        """
        self.make_form()

        # check user data
        if not self.request.user.css_url:
            self.request.user.css_url = config.css_url

        # different form elements depending on login state
        html_uid = ''
        if self.request.user.valid:
            html_uid = '<tr><td><b>ID</b>&nbsp;</td><td>%s</td></tr>' % (self.request.user.id,)
            buttons = [
                ('save', self._(' Save ')),
                ('logout', self._(' Logout ')),
            ]
#            url = "%s?action=userform&uid=%s" % (webapi.getBaseURL(), self.request.user.id)
#            html_relogin = self._('To login from a different machine, use this URL: ') + \
#                '<a href="%s">%s</a><br>' % (url, url)
        else:
            buttons = [
	        ("save", self._(' Create Profile ')),
                ('login', self._(' Login ')),
            ]
#           html_relogin = ""

            if config.mail_smarthost:
                html_uid = """
                    <tr><td><b>%s</b>&nbsp;</td><td><input type="text" size="40" name="login_email"></td></tr>
                    <tr><td></td><td><input type="submit" name="login_sendmail" value="%s"></td></tr>
                """ % (self._('Your email address'),
                       self._(' Mail me my account data '))

        self._table.append(html.Raw(html_uid))

        self.make_row(self._('Name'), [
	    html.INPUT(
                type="text", size=32, name="username", value=self.request.user.name
            ),
	    ' \xA0 ', self._('(Use FirstnameLastname)'),
	])

        self.make_row(self._('Password'), [
	    html.INPUT(
	        type="password", size=32, name="password", value=self.request.user.enc_password
	    )
	])

        self.make_row(self._('Password repeat'), [
	    html.INPUT(
	        type="password", size=32, name="password2", value=self.request.user.enc_password
            ),
            ' \xA0 ', self._('(Only when changing passwords)'),
	])

        self.make_row(self._('Email'), [html.INPUT(
            type="text", size=40, name="email", value=self.request.user.email
        )])

        self.make_row(self._('CSS URL'), [
            html.INPUT(
                type="text", size=40, name="css_url", value=self.request.user.css_url
            ),
            ' \xA0 ', self._('("None" for disabling CSS)'),
        ])

        self.make_row(self._('Editor size'), [
            html.INPUT(type="text", size=3, maxlength=3,
                name="edit_cols", value=self.request.user.edit_cols),
            ' \xA0x\xA0 ',
            html.INPUT(type="text", size=3, maxlength=3,
                name="edit_rows", value=self.request.user.edit_rows),
        ])

        self.make_row(self._('Time zone'), [
            self._('Your time is'), ' ',
            self._tz_select(),
            html.BR(),
            self._('Server time is'), ' ',
            time.strftime(config.datetime_fmt, util.datetime.tmtuple()),
            ' (UTC)',
        ])

        self.make_row(self._('Date format'), [self._dtfmt_select()])

        self.make_row(self._('Preferred language'), [self._lang_select()])

        # boolean user options
        bool_options = []
        checkbox_fields = user.User._checkbox_fields
        checkbox_fields.sort(lambda a, b: cmp(a[1](), b[1]()))
        for key, label in checkbox_fields:
            bool_options.extend([
                html.INPUT(type="checkbox", name=key, value=1,
                    checked=getattr(self.request.user, key, 0)),
                '\xA0', label(), html.BR(),
            ])
        self.make_row(self._('General options'), bool_options)

        self.make_row(self._('Quick links'), valign="top", cell=[
            html.TEXTAREA(name="quicklinks", rows=6, cols=50)
                .append('\n'.join(self.request.user.getQuickLinks())),
        ])

        # subscribed pages
        if config.mail_smarthost:
            notifylist = self.request.user.getSubscriptionList()
            notifylist.sort()

            warning = []
            if not self.request.user.email:
                warning = [
                    html.BR(),
                    html.SMALL(Class="warning").append(
                        self._("This list does not work, unless you have"
                          " entered a valid email address!")
                    )]
            
            self.make_row(
                html.Raw(self._('Subscribed wiki pages<br>(one regex per line)')),
                valign="top",
                cell=[
                    html.TEXTAREA(name="subscribed_pages", rows=6, cols=50)
                        .append('\n'.join(notifylist)),
                ] + warning
            )

        # add buttons
        button_cell = []
        for name, label in buttons:
            button_cell.extend([
                html.INPUT(type="submit", name=name, value=label),
                ' \xA0 ',
            ])
        self.make_row('', button_cell)

        return str(self._form)
# + html_relogin


def getUserForm(request):
    """ Return HTML code for the user settings.
    """
    return UserSettings(request).asHTML()


#############################################################################
### User account administration
#############################################################################

def do_user_browser(request):
    """ Browser for SystemAdmin macro.
    """
    from MoinMoin.util.dataset import TupleDataset, Column
    _ = request.getText

    data = TupleDataset()
    data.columns = [
        Column('id', label=('ID'), align='right'),
        Column('name', label=('Username')),
        Column('email', label=('Email')),
        Column('action', label=_('Action')),
    ]

    # iterate over users
    for uid in user.getUserList():
        account = user.User(request, uid)
        data.addRow((
            request.formatter.code(1) + uid + request.formatter.code(0),
            request.formatter.text(account.name),
            request.formatter.text(account.email),
            '',
        ))

    if data:
        from MoinMoin.widget.browser import DataBrowserWidget

        browser = DataBrowserWidget(request)
        browser.setData(data)
        return browser.toHTML()

    # no data
    return ''

