"""
    MoinMoin search engine
    
    @copyright: Florian Festi TODO: email
    @license: GNU GPL, see COPYING for details
"""

import re, time, sys, urllib, StringIO
#sys.path.append('..')
from MoinMoin import wikiutil, config
from MoinMoin.Page import Page

#try:
#    import xapian
#except ImportError:
#    xapian = False

#############################################################################
### query objects
#############################################################################

class BaseExpression:
    """
    Base class for all search terms
    """
    def __init__(self):
        self.negated = 0

    def __str__(self):
        return unicode(self).encode(config.charset, 'replace')

    def negate(self):
        "negate the result of this term"
        self.negated = 1 

    def search(self, page):
        """
        Searches a page. Returns a list of Match objects or
        None if term didn't find anything (viceversa if negate() was called).
        Terms containing other terms must call this method to aggregate the
        results.
        This Base class returns True (Match()) if not negated.
        """
        if self.negated:
            return [Match()]
        else:
            return None
    
    def costs(self):
        """
        estimated time to calculate this term.
        Number is is relative to other terms and has no real unit.
        It allows to do the fast searches first.
        """ 
        return 0

    def highlight_re(self):
        """
        return a regular expression of what the term searches for
        to highlight them in the found page
        """
        return ''

    def indexed_query(self):
        """
        experimental/unused may become interface to the indexing search engine
        """
        return self

    def _build_re(self, pattern, use_re=False, case=False):
        "make a regular expression out of a text pattern"
        if case: # case sensitive
            flags = re.U
        else: # ignore case
            flags = re.U + re.I
            
        if use_re:
            try:
                self.search_re = re.compile(pattern, flags)
            except re.error:
                pattern = re.escape(pattern)
                self.pattern = pattern
                self.search_re = re.compile(pattern, flags)
        else:
            pattern = re.escape(pattern)
            #pattern = pattern.replace(u'\\*', u'\S*')
            #pattern = pattern.replace(u'\\?', u'.')
            self.search_re = re.compile(pattern, flags)
            self.pattern = pattern

class AndExpression(BaseExpression):
    """
    A term connecting several subterms with a logical AND
    """

    operator = ' '

    def __init__(self, *terms):
        self._subterms = list(terms)
        self._costs = 0
        for t in  self._subterms:
            self._costs += t.costs()
        self.negated = 0

    def append(self, expression):
        "append another term"
        self._subterms.append(expression)
        self._costs += expression.costs()

    def subterms(self):
        return self._subterms
    
    def costs(self):
        return self._costs

    def __unicode__(self):
        result = ''
        for t in self._subterms:
            result += self.operator + t
        return u'[' + result[len(self.operator):] + u']'

    def search(self, page):
        self._subterms.sort(lambda x, y: cmp(x.costs(), y.costs()))
        matches = []
        for term in self._subterms:
            result = term.search(page)
            if not result:
                return None
            matches.extend(result)
        return matches

    def highlight_re(self):
        result = []
        for s in self._subterms:
            highlight_re = s.highlight_re()
            if highlight_re: result.append(highlight_re)
            
        return '|'.join(result)

    def indexed_query(self):
        indexed_terms = []
        sub_terms = []
        for term in self._subterms:
            term = term.indexed_query()
            if term is isinstance(BaseExpression):
                subterms.append(term)
            else:
                indexed_terms.append(term)

        if indexed_terms:

            if not sub_terms:
                return indexed_terms

    def indexed_search(self):
        if self.indexed_query:
            indexed_result = self.indexed_query.indexed_query()
            result = []
            for foundpage in indexed_result:
                matches = self.search(foundpage.page)
                if matches:
                    result.append(foundpage)
                    foundpage.add_matches(matches)


class OrExpression(AndExpression):
    """
    A term connecting several subterms with a logical OR
    """
    
    operator = ' or '

    def search(self, page):
        self._subterms.sort(lambda x, y: cmp(x.costs(), y.costs()))
        matches = []
        for term in self._subterms:
            result = term.search(page)
            if result:
                matches.extend(result)
        return matches

class TextSearch(BaseExpression):
    """
    A term that does a normal text search in the page content
    and the page title, too, using an additional TitleSearch term.
    """

    def __init__(self, pattern, use_re=False, case=False):
        """ Init a text search

        @param pattern: pattern to search for, ascii string or unicode
        @param use_re: treat pattern as re of plain text, bool
        @param case: do case sensitive search, bool 
        """
        self._pattern = unicode(pattern)
        self.negated = 0
        self._build_re(self._pattern,
                       use_re=use_re, case=case)
        self.titlesearch = TitleSearch(self._pattern, use_re=use_re, case=case)
        
    def costs(self):
        return 10000
    
    def __unicode__(self):
        if self.negated: neg = '-'
        else: neg = ''
        return u'%s"%s"' % (neg, unicode(self._pattern))

    def highlight_re(self):
        return u"(%s)" % self._pattern

    def search(self, page):
        body = page.get_raw_body()

        pos = 0
        fragments = self.titlesearch.search(page)
        if fragments is None: fragments = []
        while 1:
            match = self.search_re.search(body, pos)
            if not match: break
            pos = match.end()
            fragments.append(TextMatch(match.start(),match.end()))

        if ((self.negated and fragments) or
            (not self.negated and not fragments)):
            return None
        elif fragments:
            return fragments
        else:
            return [Match()]

    def indexed_query(self):
        return xapian.Query(self._pattern)

class TitleSearch(BaseExpression):
    """
    term searches in pattern in page title only
    """

    def __init__(self, pattern, use_re=False, case=False):
        """ Init a title search

        @param pattern: pattern to search for, ascii string or unicode
        @param use_re: treat pattern as re of plain text, bool
        @param case: do case sensitive search, bool 
        """
        self._pattern = pattern
        self.negated = 0
        self._build_re(unicode(pattern), use_re=use_re, case=case)
        
    def costs(self):
        return 100

    def __unicode__(self):
        if self.negated: neg = '-'
        else: neg = ''
        return u'%s!"%s"' % (neg, unicode(self._pattern))

    def highlight_re(self):
        return u"(%s)" % self._pattern    

    def search(self, page):
        match = self.search_re.search(page.page_name)
        if ((self.negated and match) or
            (not self.negated and not match)):
            return None
        elif match:
            return [TitleMatch(match.start(), match.end())]
        else:
            return [Match()]

    def indexed_query(self):
        return self
    
class IndexedQuery:
    """unused and experimental"""
    def __init__(self, queryobject):
        self.queryobject = queryobject
    def indexed_search(self):
        pass
        # return list of results
    

############################################################################
### Results
############################################################################
        

class FoundPage:
    """
    Represents a page in a search result
    """

    def __init__(self, page_name, matches=[], page=None):
        self.page_name = page_name
        self.page = page
        self._matches = matches

    def weight(self):
        """returns how important this page is for the terms searched for"""
        self._matches.sort(lambda x, y: cmp(x.start, y.start))
        weight = 0
        for match in self._matches:
            weight += match.weight()
            # more sophisticated things to be added
            # increase weight of near matches
        return weight

    def add_matches(self, matches):
        self._matches.extend(matches)

    def get_matches(self):
        return self._matches[:]



class FoundAttachment(FoundPage):
    pass

class Match:
    """
    Base class for all Matches (found pieces of pages).
    This class represents a empty True value as returned from negated searches.
    """
    def __init__(self, start=0, end=0):
        self.start = start
        self.end = end

    def __len__(self):
        return self.end - self.start

    def view(self):
        return ''

    def weight(self):
        return 1.0

class TextMatch(Match):
    """Represents a match in the page content"""
    pass

class MatchInAttachment(Match):
    """
    Represents a match in a attachment content
    Not used yet.
    """
    pass

class TitleMatch(Match):
    """
    Represents a match in the page title
    Has more weight as a match in the page content.
    """
    def weight(self):
        return 50.0

##############################################################################
### Parse Query
##############################################################################


class QueryParser:
    """
    Converts a String into a tree of Query objects
    using recursive top/down parsing
    """

    def __init__(self, **kw):
        """
        @keyword titlesearch: treat all terms as title searches
        @keyword case: do case sensitive search
        @keyword regex: treat all terms as regular expressions
        """
        self.titlesearch = kw.get('titlesearch', 0)
        self.case = kw.get('case', 0)
        self.regex = kw.get('regex', 0)

    def parse_query(self, query):
        """ transform an string into a tree of Query objects"""
        self._query = query
        result = self._or_expression()
        if result is None: result = BaseExpression()
        return result

    
    def _or_expression(self):
        result = self._and_expression()
        if self._query:
            result = OrExpression(result)
        while self._query:
            q = self._and_expression()
            if q:
                result.append(q)
        return result
            
    def _and_expression(self):
        result = None
        while not result and self._query:
            result = self._single_term()
        term = self._single_term()
        if term:
            result = AndExpression(result, term)
        else:
            return result
        term = self._single_term()
        while term:
            result.append(term)
            term = self._single_term()
        return result
                                
    def _single_term(self):
        regex = (r'(?P<NEG>-?)\s*(' +              # leading '-'
                 r'(?P<OPS>\(|\)|(or\b(?!$)))|' +  # or, (, )
                 r'(?P<MOD>(\w+:)*)' +
                 r'(?P<TERM>("[^"]+")|' +
                  r"('[^']+')|(\S+)))")             # search word itself
        self._query = self._query.strip()
        match = re.match(regex, self._query, re.U)
        if not match:
            return None
        self._query = self._query[match.end():]
        ops = match.group("OPS")
        if ops == '(':
            result = self._or_expression()
            if match.group("NEG"): restult.negate()
            return result
        elif ops == ')':
            return None
        elif ops == 'or':
            return None
        modifiers = match.group('MOD').split(":")[:-1]
        text = match.group('TERM')
        if ((text[0] == text[-1] == '"') or
            (text[0] == text[-1] == "'")): text = text[1:-1]

        title_search = self.titlesearch
        regex = self.regex
        case = self.case

        for m in modifiers:
            if "title".startswith(m):
                title_search = True
            elif "regex".startswith(m):
                regex = True
            elif "case".startswith(m):
                case = True

        if title_search:
            obj = TitleSearch(text, use_re=regex, case=case)
        else:
            obj = TextSearch(text, use_re=regex, case=case)

        if match.group("NEG"):
            obj.negate()
        return obj                


class SearchResults:
    """ Manage search results, supply different views

    Search results can hold valid search results and format them for
    many requests, until the wiki content change.

    For example, one might ask for full page list sorted from A to Z,
    and then ask for the same list sorted from Z to A. Or sort results
    by name and then by rank.
    """
    
    def __init__(self, query, hits, pages, elapsed):
        self.query = query # the query
        self.hits = hits # hits list
        self.pages = pages # number of pages searched
        self.elapsed = elapsed # search time

    # Public functions --------------------------------------------------

    def sortByWeight(self):
        """ Sorts found pages by the weight of the matches """
        self.hits.sort(lambda x, y: cmp((y.weight(), x.page_name),
                                   (x.weight(), y.page_name)))
        for page in self.hits:
            page._matches.sort(lambda x, y: cmp(y.weight(), x.weight()))

    def sortByPagename(self):
        """ Sorts a list of found pages alphabetical by page name """
        self.hits.sort(lambda x, y: cmp(x.page_name, y.page_name))    

    def stats(self, request, formatter):
        """ Return search statistics, formatted with formatter

        @param request: current request
        @param formatter: formatter to use
        @rtype: unicode
        @return formatted statistics
        """
        _ = request.getText
        f = formatter
        output = [
            f.paragraph(1),
            f.text(_("%(hits)d results out of %(pages)d pages.") % {
            'hits': len(self.hits), 'pages': self.pages}),
            u' (%s)' % f.text(_("%.2f seconds") % self.elapsed),
            f.paragraph(0),
            ]
        return ''.join(output)

    def pageList(self, request, formatter, info=0, numbered=1):
        """ Format a list of found pages

        @param request: current request
        @param formatter: formatter to use
        @param info: show match info in title
        @param numbered: use numbered list for display
        @rtype: unicode
        @return formatted page list
        """
        self._reset(request, formatter)
        f = formatter
        write = self.buffer.write
        if numbered:
            list = f.number_list
        else:
            list = f.bullet_list

        # Add pages formatted as list
        write(list(1))
        
        for page in self.hits:
            matchInfo = ''
            if info:
                matchInfo = self.formatInfo(page)
            item = [
                f.listitem(1),
                f.pagelink(1, page.page_name, querystr=self.querystring()),
                self.formatTitle(page),
                f.pagelink(0),
                matchInfo,
                f.listitem(0),
                ]
            write(''.join(item))           
        write(list(0))

        return self.getvalue()

    def pageListWithContext(self, request, formatter, info=1, context=180,
                            maxlines=1):
        """ Format a list of found pages with context

        The default parameter values will create Google-like search
        results, as this is the most known search interface. Good
        interface is familiar interface, so unless we have much better
        solution (we don't), being like Google is the way.

        @param request: current request
        @param formatter: formatter to use
        @param info: show match info near the page link
        @param context: how many characters to show around each match. 
        @param maxlines: how many contexts lines to show. 
        @rtype: unicode
        @return formatted page list with context
        """
        self._reset(request, formatter)
        f = formatter
        write = self.buffer.write

        # Add pages formatted as definition list
        write(f.definition_list(1))       
        
        for page in self.hits:
            matchInfo = ''
            if info:
                matchInfo = self.formatInfo(page)
            item = [
                f.definition_term(1),
                f.pagelink(1, page.page_name, querystr=self.querystring()),
                self.formatTitle(page),
                f.pagelink(0),
                matchInfo,
                f.definition_term(0),
                f.definition_desc(1),
                self.matchContext(page, context, maxlines),
                f.definition_desc(0),
                ]
            write(''.join(item))
        write(f.definition_list(0))
        
        return self.getvalue()

    # Private -----------------------------------------------------------
    
    def matchContext(self, page, context, maxlines):
        """ Format search context for each matched page

        Try to show first maxlines interesting matches context.
        """
        f = self.formatter
        if not page.page:
            page.page = Page(self.request, page.page_name)
        body = page.page.get_raw_body()
        last = len(body) -1
        matches = page._matches
        lineCount = 0
        output = []
        i = 0
        start = 0

        # Skip page header if there are more than one matches
        if len(matches) > 1:
            i, start = self.firstMatchInText(body, matches)

        # Format context
        while i < len(matches) and lineCount < maxlines:
            match = matches[i]
            
            # Skip non TextMatch
            if not isinstance(match, TextMatch):
                i += 1
                continue

            # Get context range for this match
            start, end = self.contextRange(context, match, start, last)

            # Format context lines for matches. Each complete match in
            # the context will be highlighted, and if the full match is
            # in the context, we increase the index, and will not show
            # same match again on a separate line.

            output.append(f.text(u'...'))
            
            # Get the index of the first match completely within the
            # context.
            for j in xrange(0, len(matches)):
                if matches[j].start >= start:
                    break

            # Add all matches in context and the text between them                
            while 1:
                match = matches[j]
                # Append the text before match
                if match.start > start:
                    output.append(f.text(body[start:match.start]))
                # And the match
                output.append(self.formatMatch(body, match, start))
                start = match.end
                # Get next match, but only if its completely within the context
                if j < len(matches) - 1 and matches[j + 1].end <= end:
                    j += 1
                else:
                    break

            # Add text after last match and finish the line
            if match.end < end:
               output.append(f.text(body[match.end:end]))
            output.append(f.text(u'...'))
            output.append(f.linebreak(preformatted=0))

            # Increase line and point to the next match
            lineCount += 1
            i = j + 1

        output = ''.join(output)

        if not output:
            # Return the first context characters from the page text
            output = f.text(page.page.getPageText(length=context))
            output = output.strip()
            if not output:
                # This is a page with no text, only header, for example,
                # a redirect page.
                output = f.text(page.page.getPageHeader(length=context))

        return output

    def firstMatchInText(self, body, matches):
        """ 

        Skip matches from the top of the page: acl lines, processing
        instructions or comments, These matches are usually not
        interesting.

        @rtype: tuple
        @return: index of first match, start of text
        """
        # Lazy compile of class attribute on first call to this method
        if not getattr(self.__class__, 'skiplines_re', None):
            # Skip lines that starts with # or empty/whitespace lines
            self.__class__.skiplines_re = re.compile(r'(^#+.*(?:\n\s*)+)+',
                                                     re.UNICODE | re.MULTILINE)       
        start = 0
        i = 0
        match = self.skiplines_re.search(body)
        if match:
            start = match.end()
            # Find first match after start
            for i in xrange(0, len(matches)):
                if matches[i].start >= start:
                    break
        return i, start       

    def contextRange(self, context, match, start, last):
        """ Compute context range

        Add context around each match. If there is no room for context
        before or after the match, show more context on the other side.

        @param context: context length
        @param match: current match
        @param start: context should not start before that index, unless
                      end is past the last character.
        @param last: last character index
        @rtype: tuple
        @return: start, end of context
        """
        # Start by giving equal context on both sides of match
        contextlen = max(context - len(match), 0)
        cstart = match.start - contextlen / 2
        cend = match.end + contextlen / 2

        # If context start before start, give more context on end
        if cstart < start:
            cend += start - cstart
            cstart = start
            
        # But if end if after last, give back context to start
        if cend > last:
            cstart -= cend - last
            cend = last

        # Keep context start positive for very short texts
        cstart = max(cstart, 0)

        return cstart, cend

    def formatTitle(self, page):
        """ Format page title

        Invoke format match on match in title
        """
        # Get title matches and sort them by match.start
        matches = [(m.start, m) for m in page._matches
                   if isinstance(m, TitleMatch)]
        matches.sort()
        matches = [m for mstart, m in matches]

        pagename = page.page_name
        f = self.formatter
        output = []
        start = 0
        # Format
        for match in matches:
            # Write text before match and match
            if start < match.start:
                output.append(f.text(pagename[start:match.start]))
            output.append(self.formatMatch(pagename, match, start))
            start = match.end
        # Add text after match
        if start < len(pagename):
            output.append(f.text(pagename[start:]))

        return ''.join(output)
        
    def formatMatch(self, body, match, start=0):
        """ Format single match in context """
        f = self.formatter
        if start>match.end: return ""
        if start<match.start: start = match.start
        output = [
            f.strong(1),
            f.text(body[start:match.end]),
            f.strong(0),
            ]
        return ''.join(output)
        
    def querystring(self):
        """ Return query string, used in the page link """
        needle = self.query.highlight_re()
        querystr= "highlight=%s" % urllib.quote_plus(needle.encode(config.charset))
        return querystr

    def formatInfo(self, page):
        """ Return formated match info """
        # TODO: this will not work with non-html formats
        template = u'<span class="info"> . . . %s %s</span>'
        count = len(page._matches)
        info = template % (count, self.matchLabel[count != 1])
        return self.formatter.rawHTML(info)         

    def getvalue(self):
        """ Return output in div with css class """
        write = self.request.write
        # TODO: this will not work with other formatter then
        # text_html. we should add a div/section creation method to all
        # formatters.
        value = [
            self.formatter.open('div', attr={'class': 'searchresults'}),
            self.buffer.getvalue(),
            self.formatter.close('div'),
            ]
        return '\n'.join(value)

    def _reset(self, request, formatter):
        """ Update internal state before new output

        Each request might need different translations or other user preferences.
        """
        self.buffer = StringIO.StringIO()
        self.formatter = formatter
        self.request = request
        # Use 1 match, 2 matches...
        _ = request.getText    
        self.matchLabel = (_('match'), _('matches'))
            

##############################################################################
### Searching
##############################################################################

def searchPages(request, query, **kw):
    """
    Search the text of all pages for query.
    @param query: the expression we want to search for
    @rtype: SearchResults instance
    @return: search results
    """   
    from MoinMoin.Page import Page
    hits = []

    start = time.time()
    # Get user readable page list
    all_pages = request.rootpage.getPageList()

    # Search through pages
    for page_name in all_pages:
        page = Page(request, page_name)
        result = query.search(page)
        if result:
            hits.append(FoundPage(page_name, result))

    elapsed = time.time() - start    
    results = SearchResults(query, hits, len(all_pages), elapsed)
    return results
   
