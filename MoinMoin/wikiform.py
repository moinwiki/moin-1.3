"""
    MoinMoin - User Forms

    Copyright (c) 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: wikiform.py,v 1.4 2002/02/13 21:13:52 jhermann Exp $
"""

# Imports
import cgi, string
from MoinMoin import wikiutil
from MoinMoin.Page import Page
from MoinMoin.i18n import _


#############################################################################
### Form definitions
#############################################################################

_required_attributes = ['type', 'name', 'label']

def parseDefinition(fielddef, fieldlist):
    """ Parse a form field definition and return the HTML markup for it
    """
    row = '<tr><td nowrap valign="top">&nbsp;<b>%s</b>&nbsp;</td><td>%s</td></tr>\n'
    fields, msg = wikiutil.parseAttributes(fielddef)

    if not msg:
        for required in _required_attributes:
            if not fields.has_key(required):
                msg = _('Required attribute "%(attrname)s" missing')  % {
                    'attrname': required}
                break

    if msg:
        # create visible error
        result = row % (msg, fielddef)
    elif fields['type'] == '"caption"':
        # create a centered, bold italic caption
        result = '<tr><td colspan="2" align="center"><i><b>%s</b></I></td></tr>\n' % (
            fields['label'][1:-1])
    else:
        # for submit buttons, use `label` as the value
        if fields['type'] == '"submit"':
            fields['value'] = fields['label']
            fields['label'] = ''

        # make sure user cannot use a system name
        fields['name'] = '"form_' + fields['name'][1:]
        fieldlist.append(fields['name'][1:-1])

        wrapper = ('<input', '>\n')
        if fields['type'] == '"textarea"':
            wrapper = ('<textarea', '></textarea>\n')

        result = wrapper[0]
        for key, val in fields.items():
            if key == 'label': continue
            result = '%s %s=%s' % (result, key, val)
        result = result + wrapper[1]

        #result = result + cgi.escape(`fields`)

        if fields['type'] == '"submit"':
            result = '<tr><td colspan="2" align="center">%s</td></tr>\n' % result
        else:
            result = row % (fields['label'][1:-1], result)

    return result


def _get_formvalues(form):
    result = {}
    for key in form.keys():
        if key[:5] != 'form_': continue

        val = string.replace(form.getvalue(key, "<empty>"), '\r', '')
        if type(val) is type([]):
            # Multiple username fields specified
            val = string.join(val, "|")

        result[key] = val

    return result


def do_formtest(pagename, form):
    """ Test a user defined form.
    """
    msg = _('Submitted form data:') + '<ul>\n'
    for key, val in _get_formvalues(form).items():
        msg = msg + '<li><em>%s</em> = %s</li>\n' % (
            string.upper(key), repr(cgi.escape(val))
        )
    msg = msg + '</ul>\n'

    Page(pagename).send_page(form, msg=msg)

