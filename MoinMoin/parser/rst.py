"""
    MoinMoin - ReStructured Text Parser

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: rst.py,v 1.2 2002/05/09 11:27:21 jhermann Exp $
"""

import cgi, sys
from docutils import core, nodes, utils
from docutils.parsers import rst


#############################################################################
### ReStructured Text Parser
#############################################################################

class Parser:
    """ Parse RST via "docutils".
    """

    def __init__(self, raw, request, **kw):
        self.raw = raw
        self.request = request

    def format(self, formatter, form):
        """ Send the text.
        """
        #core.publish(source=self.raw, destination=sys.stdout, writer_name='html')

        parser = rst.Parser()
        document = utils.new_document()
        parser.parse(self.raw, document)

        if 1:
            document.walkabout(MoinTranslator(self.request, formatter, document))

        if 0:
            dom = document.asdom()
            print '<pre>'
            print cgi.escape(dom.toprettyxml(indent='  '))
            print '</pre>'

        if 0:
            print '<pre>'
            print cgi.escape(document.astext())
            print '</pre>'


class MoinTranslator(nodes.NodeVisitor):

    def __init__(self, request, formatter, document):
        nodes.NodeVisitor.__init__(self, document)
        self.request = request
        self.formatter = formatter

    def visit_Text(self, node):
        print self.formatter.text(node.astext())

    def depart_Text(self, node):
        pass

    def visit_title(self, node):
        print self.formatter.heading(1, node.astext())


    #
    # Text markup
    #

    def visit_emphasis(self, node):
        print self.formatter.emphasis(1)

    def depart_emphasis(self, node):
        print self.formatter.emphasis(0)

    def visit_strong(self, node):
        print self.formatter.strong(1)

    def depart_strong(self, node):
        print self.formatter.strong(0)

    def visit_literal(self, node):
        print self.formatter.code(1)

    def depart_literal(self, node):
        print self.formatter.code(0)


    #
    # Blocks
    #

    def visit_paragraph(self, node):
        #if self.topic_class != 'contents':
        print self.formatter.paragraph(1)

    def depart_paragraph(self, node):
        #if self.topic_class == 'contents':
        #    print self.formatter.linebreak()
        #else:
        print self.formatter.paragraph(0)

    def visit_literal_block(self, node):
        print self.formatter.preformatted(1)

    def depart_literal_block(self, node):
        print self.formatter.preformatted(0)


    #
    # Lists
    #

    def visit_bullet_list(self, node):
        print self.formatter.bullet_list(1)

    def depart_bullet_list(self, node):
        print self.formatter.bullet_list(0)

    def visit_enumerated_list(self, node):
        print self.formatter.number_list(1, start=node.get('start', None))

    def depart_enumerated_list(self, node):
        print self.formatter.number_list(0)

    def visit_list_item(self, node):
        print self.formatter.listitem(1)

    def depart_list_item(self, node):
        print self.formatter.listitem(0)

    def visit_definition_list(self, node):
        print self.formatter.definition_list(1)

    def depart_definition_list(self, node):
        print self.formatter.definition_list(0)


    #
    # Admonitions
    #

    def visit_warning(self, node):
        print self.formatter.highlight(1)

    def depart_warning(self, node):
        print self.formatter.highlight(0)


    #
    # Misc
    #

    def visit_system_message(self, node):
        print self.formatter.highlight(1)
        print '[%s]' % node.astext()
        print self.formatter.highlight(0)

