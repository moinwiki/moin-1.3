# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - "text/python" Formatter

    Compiles pages to executable python code.

    @copyright: 2000-2004 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import time
from MoinMoin import wikiutil

class Formatter:
    """
        Inserts '<<<>>>' into the page and adds python code to
        self.code_fragments for dynamic parts of the page
        (as macros, wikinames...).
        Static parts are formatted with an external formatter.
        Page must be assembled after the parsing to get working python code.
    """

    def __init__(self, request, static = [], formatter = None, **kw):
        if formatter:
            self.formatter = formatter
        else:
            from MoinMoin.formatter.text_html import Formatter
            self.formatter = Formatter(request, store_pagelinks=1)
        self.static = static
        self.code_fragments = []
        self.__formatter = "formatter"
        self.__parser = "parser"
        self.request = request
        self.__lang = request.current_lang
        self.__in_p = 0
        self.__in_pre = 0
        self.text_cmd_begin = '\nrequest.write('
        self.text_cmd_end = ')\n'

    def assemble_code(self, text):
        """inserts the code into the generated text
        """
        #text = text.replace('\\', '\\\\')
        #text = text.replace('"', '\\"')
        text = text.split('<<<>>>', len(self.code_fragments))
        source = self.text_cmd_begin + repr(text[0])
        i = 0
        for t in text[1:]:
            source = (source + self.text_cmd_end +
                      self.code_fragments[i] +
                      self.text_cmd_begin + repr(text[i+1]))
            i = i + 1
        source = source + self.text_cmd_end
        self.code_fragments = [] # clear code fragments to make
                                 # this object reusable
        # Automatic invalidation due to moin code changes:
        # we are called from Page.py, so moincode_timestamp is
        # mtime of MoinMoin directory. If we detect, that the
        # saved rendering code is older than the MoinMoin directory
        # we invalidate it by raising an exception. This avoids
        # calling functions that have changed by a code update.
        # Hint: we don't check the mtime of the directories within
        # MoinMoin, so better do a touch if you only modified stuff
        # in a subdirectory.
        waspcode_timestamp = int(time.time())
        source = """
moincode_timestamp = int(os.path.getmtime(os.path.dirname(__file__)))
if moincode_timestamp > %d: raise "CacheNeedsUpdate"
%s
""" % (waspcode_timestamp, source)
        return source

    def __getattr__(self, name):
        """ For every thing we have no method/attribute use the formatter
        """
        return getattr(self.formatter, name)

    def __insert_code(self, call):
        """ returns the python code
        """
        self.code_fragments.append(call)
        return '<<<>>>'

    def __is_static(self, dependencies):
        for dep in dependencies:
            if dep not in  self.static: return False
        return True

    def __adjust_languge_state(self):
        """ Add current language state changing code to the cache """
        if self.__lang != self.request.current_lang:
            self.__lang = self.request.current_lang
            return 'request.current_lang = %r\n' % self.__lang
        return ''
        
    def __adjust_formatter_state(self):
        result = self.__adjust_languge_state()
        if self.__in_p != self.formatter.in_p:
            result = "%s%s.in_p = %r\n" % (result, self.__formatter,
                                           self.formatter.in_p)
            self.__in_p = self.formatter.in_p
        if self.__in_pre != self.formatter.in_pre:
            result = "%s%s.in_pre = %r\n" % (result, self.__formatter,
                                           self.formatter.in_pre)
            self.__in_pre = self.formatter.in_pre        
        return result
    
    def dynamic_content(self, parser, callback, arg_list = [], arg_dict = {},
                            returns_content = 1):
        adjust = self.__adjust_formatter_state()
        if returns_content:
            return self.__insert_code('%srequest.write(%s.%s(*%r,**%r))' %
                        (adjust, self.__parser, callback, arg_list, arg_dict))
        else:
            return self.__insert_code('%s%s.%s(*%r,**%r)' %
                        (adjust, self.__parser, callback, arg_list, arg_dict))

    # Public methods ---------------------------------------------------
        
    def pagelink(self, on, pagename='', page=None, **kw):
        if on:
            return self.__insert_code('page=Page(request, %r, formatter=%s);'
                                      'request.write(%s.pagelink(%r, page=page, **%r))' %
                                      (pagename, self.__formatter,
                                       self.__formatter, on, kw))
        else:
            return self.__insert_code('request.write(%s.pagelink(%r, page=page, **%r))' %
                                      (self.__formatter, on, kw))

    def attachment_link(self, on, url='', **kw):
        return self.__insert_code(
            'request.write(%s.attachment_link(%r, %r, **%r))' %
            (self.__formatter, on, url, kw))
    def attachment_image(self, url, **kw):
        return self.__insert_code(
            'request.write(%s.attachment_image(%r, **%r))' %
            (self.__formatter, url, kw))
    
    def attachment_drawing(self, url, **kw):
        return self.__insert_code(
            'request.write(%s.attachment_drawing(%r, **%r))' %
            (self.__formatter, url, kw))
    
    def attachment_inlined(self, url, **kw):
        return self.__insert_code(
            'request.write(%s.attachment_inlined(%r, **%r))' %
            (self.__formatter, url, kw))

    def heading(self, on, depth, **kw):        
        if on:
            code = [
                self.__adjust_languge_state(),
                'request.write(%s.heading(%r, %r, **%r))' % (self.__formatter,
                                                             on, depth, kw),
                ]     
            return self.__insert_code(''.join(code))
        else:
            return self.formatter.heading(on, depth, **kw)

    def icon(self, type):
        if self.__is_static(['user']):
            return self.formatter.icon(type)
        else:
            return self.__insert_code('request.write(%s.icon(%r))' %
                                      (self.__formatter, type))

    def macro(self, macro_obj, name, args):
        if self.__is_static(macro_obj.get_dependencies(name)):
            return macro_obj.execute(name, args)
        else:
            return self.__insert_code(
                '%srequest.write(%s.macro(macro_obj, %r, %r))' %
                (self.__adjust_formatter_state(),
                 self.__formatter, name, args))
            
    def processor(self, processor_name, lines, is_parser = 0):
        """ processor_name MUST be valid!
        prints out the result insted of returning it!
        """
        if not is_parser:
            Dependencies = wikiutil.importPlugin(self.request.cfg, "processor",
                                                 processor_name, "Dependencies")
        else:
            Dependencies = wikiutil.importPlugin(self.request.cfg, "parser",
                                                 processor_name, "Dependencies")
            
        if Dependencies == None:
            Dependencies = ["time"]
        if self.__is_static(Dependencies):
            return self.formatter.processor(processor_name, lines, is_parser)
        else:
            return self.__insert_code('%s%s.processor(%r, %r, %r)' %
                                      (self.__adjust_formatter_state(),
                                       self.__formatter,
                                       processor_name, lines, is_parser))

