# -*- coding: iso-8859-1 -*-
"""
    MoinMoin Group Functions

    Written 2003 by Thomas Waldmann, http://linuxwiki.de/ThomasWaldmann
    and Gustavo Niemeyer, http://moin.conectiva.com.br/GustavoNiemeyer

    GNU GPL licensed

    $Id: wikigroup.py,v 1.3 2003/11/09 21:00:52 thomaswaldmann Exp $
"""
__version__ = "$Revision: 1.3 $"[11:-2]

import re, pickle, time
from MoinMoin import config, wikiutil, Page

GROUPS_PICKLE_VERSION = 1

class Group:
    """a Group - e.g. of users, of pages, of whatever

       How a Group definition page should look like:

       any text does not care
        * member1
         * does not care, too
        * member2
        * ....
        * memberN
       any text does not care

       if there are any free links using ["free link"] notation, the markup
       is stripped when the group list is built 
    """

    def __init__(self, name):
        """Initialize a Group, starting from <nothing>.
        """
        self.name = name
        self._members = []
        p = Page.Page(name)
        text = p.get_raw_body()
        for line in text.split("\n"):
            if line.startswith(" * "):
	        member = line[3:].strip()
		if member.startswith('["') and member.endswith('"]'):
		    member = member[2:-2]
                self.addmember(member)

    def members(self):
        return self._members

    def addmembers(self, members):
        self._members.extend(members)

    def addmember(self, member):
        self._members.append(member)

    def hasmember(self, what):
        return what in self._members

    def _expandgroup(self, groupdict, name):
        groupmembers = groupdict.members(name)
        members = []
        for member in groupmembers:
            if member == self.name:
                continue
            if groupdict.hasgroup(member):
                members.extend(self._expandgroup(groupdict, member))
            else:
                members.append(member)
        return members

    def expandgroups(self, groupdict):
        members = []
        for member in self._members:
            if member == self.name:
                continue
            if groupdict.hasgroup(member):
                members.extend(self._expandgroup(groupdict, member))
            else:
                members.append(member)
        self._members = members

class GroupDict:
    """a dictionary of Group objects

       Config:
           config.page_group_regex
               Default: ".*Group$"
    """

    def __init__(self):
        """Initialize a Group, starting from <nothing>.
        """
        self.reset()

    def reset(self):
        self.groupdict = {}
        self.timestamp = 0
        self.picklever = GROUPS_PICKLE_VERSION

    def hasmember(self, groupname, member):
        group = self.groupdict.get(groupname)
        if group and group.hasmember(member):
            return 1
        return 0

    def members(self, groupname):
        """get members of group <groupname>"""
        try:
            group = self.groupdict[groupname]
        except KeyError:
            return []
        return group.members()

    def addgroup(self, groupname):
        """add a new group (will be read from the wiki page)"""
        self.groupdict[groupname] = Group(groupname)

    def hasgroup(self, groupname):
        return self.groupdict.has_key(groupname)

    def membergroups(self, member):
        """list all groups where member is a member of"""
        grouplist = []
        for group in self.groupdict.values():
            if group.hasmember(member):
                grouplist.append(group.name)
        return grouplist

    def scangroups(self):
        """scan all pages matching the group regex and init the groupdict"""
        dump = 0
        picklefile = config.data_dir + '/groups.pickle'
        try:
            data = pickle.load(open(picklefile))
            self.groupdict = data["groupdict"]
            self.timestamp = data["timestamp"]
            self.picklever = data["picklever"]
            if self.picklver != GROUPS_PICKLE_VERSION:
                self.reset()
                dump = 1
        except:
            self.reset()

        now = time.time()
        if now - self.timestamp > 60:
            group_re = re.compile(config.page_group_regex)
            pagelist = filter(group_re.match,
                              wikiutil.getPageList(config.text_dir))
            for pagename in pagelist:
                if not self.groupdict.has_key(pagename):
                    self.addgroup(pagename)
            # Force dump, to update the timestamp
            dump = 1
        for pagename in self.groupdict.keys():
            if Page.Page(pagename).mtime() > self.timestamp:
                self.addgroup(pagename)
                dump = 1
        self.timestamp = now
        if dump:
            for group in self.groupdict.values():
                group.expandgroups(self)
            data = {
                "timestamp": self.timestamp,
                "groupdict": self.groupdict,
                "picklever": self.picklever,
            }
            pickle.dump(data, open(picklefile, 'w'))

if __name__ == "__main__":
    import pprint
    pp=pprint.PrettyPrinter()
    
    g = Group()
#    print g.members
    g.addmember("newmember")
#    print g.members

#    print g.hasmember("member1")
#    print g.hasmember("member71")

    gd = GroupDict()
    gd.scangroups()

    print gd.members("TestGroup")
#    print gd.members("LinuxUserGroup")
#    print gd.members("SystemPagesGroup")

#    print gd.groupdict

