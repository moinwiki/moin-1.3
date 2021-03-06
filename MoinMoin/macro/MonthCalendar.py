"""
    MoinMoin - MonthCalendar Macro

    You can use this macro to put a month's calendar page on a Wiki page.

    The days are links to Wiki pages following this naming convention:
    BasePageName/year-month-day

    @copyright: 2002-2005 by Thomas Waldmann <ThomasWaldmann@gmx.de>
    @license: GNU GPL - see COPYING for details.

    Revisions:
    * first revision without a number (=1.0):
        * was only online for a few hours and then replaced by 1.1
    * 1.1:
        * changed name to MonthCalendar to avoid conflict with "calendar" under case-insensitive OSes like Win32
        * days as subpages
        * basepage argument
        * change order of year/month argument
        * browsing links to prev/next month/year
            * current limitation: you can only browse one calendar on the same
              page/url, if you try to browse another calendar on the same page,
              the first one jumps back to its original display
    * show basepage in calendar header if basepage<>currentpage
    * 1.2:
        * minor fixes in argument parsing
        * cosmetic fix for netscape, other cosmetic changes, changed css
        * i18n support (weekday short names)
    * 1.3:
        * fixes to run with MoinMoin 0.11, thanks to JuergenHermann
        * fix: withspace before "," allowed in argument list
        * BasePage in calendar header (if present) is a link now
        * more i18n
        * HTML cleanup, generating code avoids bracketing errors
        * colour cosmetics
    * 1.4:
        * new parameter for enabling fixed height of 6 "calendar weeks",
          if you want to show a whole year's calendar, this just looks
          better than having some months with 4, some with 5 and some with 6.
        * group calendaring functions:
          * you can give mutliple BasePages UserName1*UserName2*UserName3
          * first BasePage is considered "your" Basepage,
            used days are bright red
          * 2nd and all other BasePages are considered "others" BasePages
            and lead to an increasing green component the more "used" days
            the others have. So white gets greener and red gets more yellowish.
          * in the head part of the calendar, you can click on each name
            to get to the Page of the same name
          * colouring of my and others BasePage is done in a way to show
            the colouring used in the calendar:
          * others use green colouring (increasingly green if multiply used)
          * I use red colouring, which gets more and more yellowish as
            the day is used by more and more others, too
    * 1.5:
        * fixed username colouring when using a BasePage
        * fixed navigation header of MonthCalendar not to get broken into
          multiple lines
        * fixed SubPage handling (please do not use relative SubPages like
          /SubPage yet. Use MyName/SubPage.)
    * 1.6:
        * syntactic cleanup
        * removed i18n compatibility for moin<1.1 or cvs<2003-06-10
        * integrated Scott Chapman's changes:
            * Made it configurable for Sunday or Monday as the first day of the week.
              Search for "change here".
            * Made it so that today is not only set to a seperate css style, but also boldfaced.
              Some browsers don't show the other css style (Netscape).
            * Made it so weekend dates have different color.
    * 1.7:
        * added request parameter where needed
    * 1.8:
        * some fixes for moin 1.2 (use this version ONLY if you run moin 1.2, too):
            * .value backtrace fixed when selecting next/prev month/year
            * request param added to macro function
    * 1.9:
        * adapted to moin 1.3
    * 2.0:
        * integrated into moin 1.3
        * added some nice JS (thanks to Klaus Knopper) to show nice mouseovers
          showing a preview of the day page linked (use first level headlines
          to make entries)
        * merged "common navigation" change of OliverGraf
        * merged AnnualMonthlyCalendar change of JonathanDietrich
    * 2.1:
        * fixed CSS for IE users
        * fix javascript for IE4
        * do a correct calculation of "today" using user's timezone


    Usage:
        [[MonthCalendar(BasePage,year,month,monthoffset,monthoffset2,height6)]]

        each parameter can be empty and then defaults to currentpage or currentdate or monthoffset=0

    Samples (paste that to one of your pages for a first try):

Calendar of current month for current page:
[[MonthCalendar]]

Calendar of last month:
[[MonthCalendar(,,,-1)]]

Calendar of next month:
[[MonthCalendar(,,,+1)]]

Calendar of Page SampleUser, this years december:
[[MonthCalendar(SampleUser,,12)]]

Calendar of current Page, this years december:
[[MonthCalendar(,,12)]]

Calendar of December, 2001:
[[MonthCalendar(,2001,12)]]

Calendar of the month two months after December, 2001
(maybe doesn't make much sense, but is possible)
[[MonthCalendar(,2001,12,+2)]]

Calendar of year 2002 (every month padded to height of 6):
||||||Year 2002||
||[[MonthCalendar(,2002,1,,,1)]]||[[MonthCalendar(,2002,2,,,1)]]||[[MonthCalendar(,2002,3,,,1)]]||
||[[MonthCalendar(,2002,4,,,1)]]||[[MonthCalendar(,2002,5,,,1)]]||[[MonthCalendar(,2002,6,,,1)]]||
||[[MonthCalendar(,2002,7,,,1)]]||[[MonthCalendar(,2002,8,,,1)]]||[[MonthCalendar(,2002,9,,,1)]]||
||[[MonthCalendar(,2002,10,,,1)]]||[[MonthCalendar(,2002,11,,,1)]]||[[MonthCalendar(,2002,12,,,1)]]||

Current calendar of me, also showing entries of A and B:
[[MonthCalendar(MyPage*TestUserA*TestUserB)]]

SubPage calendars:
[[MonthCalendar(MyName/CalPrivate)]]
[[MonthCalendar(MyName/CalBusiness)]]
[[MonthCalendar(MyName/CalBusiness*MyName/CalPrivate)]]


Anniversary Calendars: (no year data)
[[MonthCalendar(Yearly,,,+1,,6,1)]]

This creates calendars of the format Yearly/MM-DD 
By leaving out the year, you can set birthdays, and anniversaries in this 
calendar and not have to re-enter each year.
"""

Dependencies = ['namespace','time']

from MoinMoin import wikiutil
from MoinMoin.Page import Page
import re, calendar, time

# The following line sets the calendar to have either Sunday or Monday as
# the first day of the week. Only SUNDAY or MONDAY (case sensitive) are
# valid here.  All other values will not make good calendars.
# If set to Sunday, the calendar is displayed at "March 2003" vs. "2003 / 3" also.
# XXX change here ----------------vvvvvv
calendar.setfirstweekday(calendar.MONDAY)

infobox_js = r"""
//
// Bubblehelp infoboxes, (C) 2002 Klaus Knopper <infobox@knopper.net>
// You can copy/modify and distribute this code under the conditions
// of the GNU GENERAL PUBLIC LICENSE Version 2.
//
var IWIDTH=350  // Tip box width
var ie4         // Are we using Internet Explorer Version 4?
var ie5         // Are we using Internet Explorer Version 5 and up?
var kon         // Are we using KDE Konqueror?
var x,y,winW,winH  // Current help position and main window size
var idiv=null   // Pointer to infodiv container

function nsfix(){setTimeout("window.onresize = rebrowse", 2000);}

function rebrowse(){window.location.reload();}

function hascss(){ return gettip('infodiv')?true:false }

function infoinit(){
 ie4=(document.all)?true:false;
 ie5=((ie4)&&((navigator.userAgent.indexOf('MSIE 5')>0)||(navigator.userAgent.indexOf('MSIE 6')>0)))?true:false;
 kon=(navigator.userAgent.indexOf('konqueror')>0)?true:false;
 x=0;y=0;winW=800;winH=600;
 idiv=null;
 document.onmousemove = mousemove;
 // Workaround for just another netscape bug: Fix browser confusion on resize
 // obviously conqueror has a similar problem :-(
 if(kon){ nsfix() }
}

function untip(){
 if(idiv) idiv.visibility="hidden";
 idiv=null;
}

function gettip(name){return (document.layers&&document.layers[name])?document.layers[name]:(document.all&&document.all[name]&&document.all[name].style)?document.all[name].style:document[name]?document[name]:(document.getElementById(name)?document.getElementById(name).style:0);}

// Prepare tip boxes, but don't show them yet
function maketip(name,title,text){
 if(hascss()) document.write('<div id="'+name+'" name="'+name+'" style="position:absolute; visibility:hidden; z-index:20; top:-999em; left:0px;"><table width='+IWIDTH+' class="tip"><tr><th class="tip">'+title+'</th></tr><tr><td class="tip">'+text+'</td></tr></table></div>\n');
}

function tip(name){
 if(hascss()){
  if(idiv) untip();
  idiv=gettip(name);
  if(idiv){
   winW=(window.innerWidth)? window.innerWidth+window.pageXOffset-16:document.body.offsetWidth-20;
   winH=(window.innerHeight)?window.innerHeight+window.pageYOffset  :document.body.offsetHeight;
   if(x<=0||y<=0){ // konqueror can't get mouse position
    x=(winW-IWIDTH)/2+(window.pageXOffset?window.pageXOffset:0); y=(winH-50)/2+(window.pageYOffset?window.pageYOffset:0); // middle of window
   }
   showtip();
  }
 }
}

function showtip(){
  idiv.left=(((x+IWIDTH+10)<winW)?x+12:x-IWIDTH-5)+"px"; idiv.top=(((y+90)<winH)?y+12:y-90)+"px";
  idiv.visibility="visible";
//  window.status="idiv="+idiv+"X:"+(idiv.left?idiv.left:"NAN")+", Y:"+(idiv.top?idiv.top:"NAN")+", x:"+x+", y:"+y;
}

function mousemove(e){
 if(e)   {x=e.pageX?e.pageX:e.clientX?e.clientX:0; y=e.pageY?e.pageY:e.clientY?e.clientY:0;}
 else if(event) {x=event.clientX; y=event.clientY;}
 else {x=0; y=0;}
 if((ie4||ie5) && document.documentElement) // Workaround for scroll offset of IE
  {
    x+=document.documentElement.scrollLeft;
    y+=document.documentElement.scrollTop;
  }
 if(idiv) showtip();
}

// Initialize after loading the page
window.onload=infoinit;

// EOF infobox.js
"""

def cliprgb(r,g,b): # don't use 255!
    if r < 0:   r=0
    if r > 254: r=254
    if b < 0:   b=0
    if b > 254: b=254
    if g < 0:   g=0
    if g > 254: g=254
    return r, g, b

def yearmonthplusoffset(year, month, offset):
    month = month+offset
    # handle offset and under/overflows - quick and dirty, yes!
    while month < 1:
        month = month + 12
        year = year - 1
    while month > 12:
        month = month - 12
        year = year + 1
    return year, month

def parseargs(args, defpagename, defyear, defmonth, defoffset, defoffset2, defheight6, defanniversary):
    strpagename = args.group('basepage')
    if strpagename:
        parmpagename = wikiutil.unquoteWikiname(strpagename)
    else:
        parmpagename = defpagename
    # multiple pagenames separated by "*" - split into list of pagenames
    parmpagename = re.split(r'\*', parmpagename)

    stryear = args.group('year')
    if stryear:
        parmyear = int(stryear)
    else:
        parmyear = defyear

    strmonth = args.group('month')
    if strmonth:
        parmmonth = int(strmonth)
    else:
        parmmonth = defmonth
    
    stroffset = args.group('offset')
    if stroffset:
        parmoffset = int(stroffset)
    else:
        parmoffset = defoffset

    stroffset2 = args.group('offset2')
    if stroffset2:
        parmoffset2 = int(stroffset2)
    else:
        parmoffset2 = defoffset2

    strheight6 = args.group('height6')
    if strheight6:
        parmheight6 = int(strheight6)
    else:
        parmheight6 = defheight6

    stranniversary = args.group('anniversary')
    if stranniversary:
            parmanniversary = int(stranniversary)
    else:
        parmanniversary = defanniversary

    return parmpagename, parmyear, parmmonth, parmoffset, parmoffset2, parmheight6, parmanniversary
        
# FIXME:                          vvvvvv is there a better way for matching a pagename ?
_arg_basepage = r'\s*(?P<basepage>[^, ]+)?\s*'
_arg_year = r',\s*(?P<year>\d+)?\s*'
_arg_month = r',\s*(?P<month>\d+)?\s*'
_arg_offset = r',\s*(?P<offset>[+-]?\d+)?\s*'
_arg_offset2 = r',\s*(?P<offset2>[+-]?\d+)?\s*'
_arg_height6 = r',\s*(?P<height6>[+-]?\d+)?\s*'
_arg_anniversary =  r',\s*(?P<anniversary>[+-]?\d+)?\s*'
_args_re_pattern = r'^(%s)?(%s)?(%s)?(%s)?(%s)?(%s)?(%s)?$' % \
                     (_arg_basepage,_arg_year,_arg_month, \
                      _arg_offset,_arg_offset2,_arg_height6,_arg_anniversary)


def execute(macro, text):
    request = macro.request
    formatter = macro.formatter
    _ = request.getText

    # return immediately if getting links for the current page
    if request.mode_getpagelinks:
        return ''

    args_re=re.compile(_args_re_pattern)
    
    currentyear, currentmonth, currentday, h, m, s, wd, yd, ds = request.user.getTime(time.time())
    thispage = formatter.page.page_name
    # does the url have calendar params (= somebody has clicked on prev/next links in calendar) ?
    if macro.form.has_key('calparms'):
        text2 = macro.form['calparms'][0]
        args2 = args_re.match(text2)
        if not args2:
            return ('<p><strong class="error">%s</strong></p>' % _('Invalid MonthCalendar calparms "%s"!')) % (text2,)
        else:
            has_calparms = 1 # yes!
            cparmpagename, cparmyear, cparmmonth, cparmoffset, cparmoffset2, cparmheight6, cparmanniversary = \
                parseargs(args2, thispage, currentyear, currentmonth, 0, 0, 0, 0)
    else:
        has_calparms = 0

    if text is None: # macro call without parameters
        parmpagename, parmyear, parmmonth, parmoffset, parmoffset2, parmheight6, anniversary = \
            [thispage], currentyear, currentmonth, 0, 0, 0, 0
    else:
        # parse and check arguments
        args = args_re.match(text)
        if not args:
            return ('<p><strong class="error">%s</strong></p>' % _('Invalid MonthCalendar arguments "%s"!')) % (text,)
        else:
            parmpagename, parmyear, parmmonth, parmoffset, parmoffset2, parmheight6, anniversary = \
                parseargs(args, thispage, currentyear, currentmonth, 0, 0, 0, 0)

    # does url have calendar params and is THIS the right calendar to modify (we can have multiple
    # calendars on the same page)?
    #if has_calparms and (cparmpagename,cparmyear,cparmmonth,cparmoffset) == (parmpagename,parmyear,parmmonth,parmoffset):
    
    # move all calendars when using the navigation:
    if has_calparms and cparmpagename == parmpagename:
        year,month = yearmonthplusoffset(parmyear, parmmonth, parmoffset + cparmoffset2)
        parmoffset2 = cparmoffset2
    else:
        year,month = yearmonthplusoffset(parmyear, parmmonth, parmoffset)

    # get the calendar
    monthcal = calendar.monthcalendar(year, month)

    # european / US differences
    months = ('January','February','March','April','May','June','July','August','September','October','November','December')
    # Set things up for Monday or Sunday as the first day of the week
    if calendar.firstweekday() == calendar.MONDAY:
        wkend = (5, 6)
        wkdays = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
    if calendar.firstweekday() == calendar.SUNDAY:
        wkend = (0, 6)
        wkdays = ('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')

    colorstep = 85
    p = Page(request, thispage)
    qpagenames = '*'.join(map(wikiutil.quoteWikinameURL, parmpagename))
    querystr = "calparms=%%s,%d,%d,%d,%%d" % (parmyear, parmmonth, parmoffset)
    prevlink  = p.url(request, querystr % (qpagenames, parmoffset2 - 1))
    nextlink  = p.url(request, querystr % (qpagenames, parmoffset2 + 1))
    prevylink = p.url(request, querystr % (qpagenames, parmoffset2 - 12))
    nextylink = p.url(request, querystr % (qpagenames, parmoffset2 + 12))
    prevmonth = formatter.url(1, prevlink, 'cal-link') + '&lt;' + formatter.url(0)
    nextmonth = formatter.url(1, nextlink, 'cal-link') + '&gt;' + formatter.url(0)
    prevyear  = formatter.url(1, prevylink, 'cal-link') + '&lt;&lt;' + formatter.url(0)
    nextyear  = formatter.url(1, nextylink, 'cal-link') + '&gt;&gt;' + formatter.url(0)
    
    if parmpagename != [thispage]:
        pagelinks = ''
        r, g, b = (255, 0, 0)
        l = len(parmpagename[0])
        steps = len(parmpagename)
        maxsteps = (255 / colorstep)
        if steps > maxsteps:
            steps = maxsteps
        chstep = int(l / steps)
        st = 0
        while st < l:
            ch = parmpagename[0][st:st+chstep]
            r, g, b = cliprgb(r, g, b)
            pagelinks = pagelinks + '<a style="%s" href="%s">%s</a>' % \
                ('background-color:#%02x%02x%02x;color:#000000;text-decoration:none' % \
                    (r,g,b), Page(request, parmpagename[0]).url(request), ch)
            r, g, b = (r, g+colorstep, b)
            st = st + chstep
        r, g, b = (255-colorstep, 255, 255-colorstep)
        for page in parmpagename[1:]:
            pagelinks = pagelinks + '*<a style="%s" href="%s">%s</a>' % \
                            ('background-color:#%02x%02x%02x;color:#000000;text-decoration:none' % \
                                (r,g,b), Page(request, page).url(request), page)
        showpagename = '   %s<BR>\n' % pagelinks
    else:
        showpagename = ''
    if calendar.firstweekday() == calendar.SUNDAY:
        resth1 = '  <th colspan="7" class="cal-header">\n' \
                 '%s' \
                 '   %s&nbsp;%s&nbsp;<b>&nbsp;%s&nbsp;%s</b>&nbsp;%s\n&nbsp;%s\n' \
                 '  </th>\n' % (showpagename, prevyear, prevmonth, months[month-1], str(year), nextmonth, nextyear)
    if calendar.firstweekday() == calendar.MONDAY:
        resth1 = '  <th colspan="7" class="cal-header">\n' \
                 '%s' \
                 '   %s&nbsp;%s&nbsp;<b>&nbsp;%s&nbsp;/&nbsp;%s</b>&nbsp;%s\n&nbsp;%s\n' \
                 '  </th>\n' % (showpagename, prevyear, prevmonth, str(year), month, nextmonth, nextyear)
    restr1 = ' <tr>\n%s </tr>\n' % resth1

    r7 = range(7)
    restd2 = []
    for wkday in r7:
        wday = _(wkdays[wkday])
        if wkday in wkend:
            cssday = "cal-weekend"
        else:
            cssday = "cal-workday"
        restd2.append('  <td class="%s" width="14%%">%s</td>\n' % (cssday, wday))
    restr2 = ' <tr>\n%s </tr>\n' % "".join(restd2)
 
    if parmheight6:
        while len(monthcal) < 6:
            monthcal = monthcal + [[0,0,0,0,0,0,0]]

    maketip_js = []
    restrn = []
    for week in monthcal:
        restdn = []
        for wkday in r7:
            day = week[wkday]
            if not day:
                restdn.append('  <td class="cal-invalidday">&nbsp;</td>\n')
            else:
                page = parmpagename[0]
                if anniversary:
                    link = "%s/%02d-%02d" % (page, month, day)
                else:
                    link = "%s/%4d-%02d-%02d" % (page, year, month, day)
                daypage = Page(request, link)
                if daypage.exists():
                    csslink = "cal-usedday"
                    r, g, b, u = (255, 0, 0, 1)
                    daycontent = daypage.get_raw_body()
                    header1_re = re.compile(r'^\s*=\s(.*)\s=$', re.MULTILINE) # re.UNICODE
                    titletext = []
                    for match in header1_re.finditer(daycontent):
                        if match:
                            titletext.append(match.group(1))
                    tipname = link
                    tiptitle = link
                    tiptext = '<br>'.join(titletext)
                    maketip_js.append("maketip('%s','%s','%s');" % (tipname, tiptitle, tiptext))
                    onmouse = '''onMouseOver="tip('%s')" onMouseOut="untip()"''' % tipname
                else:
                    csslink = "cal-emptyday"
                    r, g, b, u = (255, 255, 255, 0)
                    if wkday in wkend:
                        csslink = "cal-weekend"
                    onmouse = ''
                for otherpage in parmpagename[1:]:
                    otherlink = "%s/%4d-%02d-%02d" % (otherpage, year, month, day)
                    otherdaypage = Page(request, otherlink)
                    if otherdaypage.exists():
                        csslink = "cal-usedday"
                        if u == 0:
                            r, g, b = (r-colorstep, g, b-colorstep)
                        else:
                            r, g, b = (r, g+colorstep, b)
                r, g, b = cliprgb(r, g, b)
                style = 'background-color:#%02x%02x%02x' % (r, g, b)
                fmtlink = formatter.url(1, daypage.url(request), csslink, attrs=onmouse) + str(day) + formatter.url(0)
                if day == currentday and month == currentmonth and year == currentyear:
                    cssday = "cal-today"
                    fmtlink = "<b>%s</b>" % fmtlink # for browser with CSS probs
                else:
                    cssday = "cal-nottoday"
                restdn.append('  <td style="%s" class="%s">%s</td>\n' % (style, cssday, fmtlink))
        restrn.append(' <tr>\n%s </tr>\n' % "".join(restdn))

    restable = '<table border="2" cellspacing="2" cellpadding="2">\n%s%s%s</table>\n'
    restable = restable % (restr1, restr2, "".join(restrn))

    result = """\
<script language="JavaScript" type="text/javascript">
<!--
%s
// -->
</script>
<div id="infodiv" style="position:absolute; visibility:hidden; z-index:20; top:-999em; left:0px;"></div>
<script language="JavaScript" type="text/javascript">
<!--
%s
// -->
</script>
%s
""" % (infobox_js, "\n".join(maketip_js), restable)
    return formatter.rawHTML(result)

# EOF

