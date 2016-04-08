# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - ReStructured Text Parser

    Copyright (c) 2002 by J�rgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: rst.py,v 1.8 2003/11/09 21:01:05 thomaswaldmann Exp $
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
        self.form = request.form
        self._ = request.getText

    def format(self, formatter):
        """ Send the text.
        """
        #core.publish(source=self.raw, destination=sys.stdout, writer_name='html')

        parser = rst.Parser()
        document = utils.new_document(None)
        if hasattr(document, 'settings'):
            document.settings.tab_width = 8
            document.settings.pep_references = None
            document.settings.rfc_references = None
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


class MoinTranslator(nodes.GenericNodeVisitor):

    def __init__(self, request, formatter, document):
        nodes.NodeVisitor.__init__(self, document)
        self.request = request
        self.formatter = formatter
        self.level = 0

    def default_visit(self, node):
        #self.default_visit(node)
        self.request.write(self.formatter.highlight(1))
        self.request.write(self.formatter.preformatted(1))
        self.request.write(self.formatter.text(node.pformat('\xA0\xA0\xA0\xA0', 1)))
        self.request.write(self.formatter.preformatted(0))
        self.request.write(self.formatter.text(node.astext()))
        self.request.write(self.formatter.highlight(0))

    def default_departure(self, node):
        pass

    def visit_document(self, node):
        pass

    def visit_section(self, node):
        self.level += 1

    def depart_section(self, node):
        self.level -= 1

    def visit_Text(self, node):
        self.request.write(self.formatter.text(node.astext()))

    def visit_title(self, node):
        self.request.write(self.formatter.heading(self.level, '', on=1))

    def depart_title(self, node):
        self.request.write(self.formatter.heading(self.level, '', on=0))


    #
    # Text markup
    #

    def visit_emphasis(self, node):
        self.request.write(self.formatter.emphasis(1))

    def depart_emphasis(self, node):
        self.request.write(self.formatter.emphasis(0))

    def visit_strong(self, node):
        self.request.write(self.formatter.strong(1))

    def depart_strong(self, node):
        self.request.write(self.formatter.strong(0))

    def visit_literal(self, node):
        self.request.write(self.formatter.code(1))

    def depart_literal(self, node):
        self.request.write(self.formatter.code(0))


    #
    # Blocks
    #

    def visit_paragraph(self, node):
        #if self.topic_class != 'contents':
        self.request.write(self.formatter.paragraph(1))

    def depart_paragraph(self, node):
        #if self.topic_class == 'contents':
        #    self.request.write(self.formatter.linebreak())
        #else:
        self.request.write(self.formatter.paragraph(0))

    def visit_literal_block(self, node):
        self.request.write(self.formatter.preformatted(1))

    def depart_literal_block(self, node):
        self.request.write(self.formatter.preformatted(0))


    #
    # Simple Lists
    #

    def visit_bullet_list(self, node):
        self.request.write(self.formatter.bullet_list(1))

    def depart_bullet_list(self, node):
        self.request.write(self.formatter.bullet_list(0))

    def visit_enumerated_list(self, node):
        self.request.write(self.formatter.number_list(1, start=node.get('start', None)))

    def depart_enumerated_list(self, node):
        self.request.write(self.formatter.number_list(0))

    def visit_list_item(self, node):
        self.request.write(self.formatter.listitem(1))

    def depart_list_item(self, node):
        self.request.write(self.formatter.listitem(0))


    #
    # Definition List
    #

    def visit_definition_list(self, node):
        self.request.write(self.formatter.definition_list(1))

    def visit_definition_list_item(self, node):
        pass

    def visit_term(self, node):
        self.request.write('<dt>')

    def depart_term(self, node):
        self.request.write('</dt>')

    def visit_definition(self, node):
        self.request.write('<dd>')

    def depart_definition(self, node):
        self.request.write('</dd>')

    def depart_definition_list(self, node):
        self.request.write(self.formatter.definition_list(0))


    #
    # Block Quote
    #

    def visit_block_quote(self, node):
        self.request.write(self.formatter.definition_list(1))

    def depart_block_quote(self, node):
        self.request.write(self.formatter.definition_list(0))


    #
    # Field List
    #

    def visit_field_list(self, node):
        self.request.write(self.formatter.bullet_list(1))

    def visit_field(self, node):
        self.request.write(self.formatter.listitem(1))

    def visit_field_name(self, node):
        self.request.write(self.formatter.strong(1))

    def depart_field_name(self, node):
        self.request.write(': ' + self.formatter.strong(0))

    def visit_field_body(self, node):
        pass

    def depart_field(self, node):
        self.request.write(self.formatter.listitem(0))

    def depart_field_list(self, node):
        self.request.write(self.formatter.bullet_list(0))


    #
    # Links
    #

    def visit_reference(self, node):
        self.request.write(self.formatter.highlight(1))
        self.request.write('&lt;&lt;&lt;')

    def depart_reference(self, node):
        self.request.write('&gt;&gt;&gt;')
        self.request.write(self.formatter.highlight(0))


    #
    # Admonitions
    #

    def visit_warning(self, node):
        self.request.write(self.formatter.highlight(1))

    def depart_warning(self, node):
        self.request.write(self.formatter.highlight(0))


    #
    # Misc
    #

    def visit_system_message(self, node):
        self.request.write(self.formatter.highlight(1))
        self.request.write('[%s]' % node.astext())
        self.request.write(self.formatter.highlight(0))


