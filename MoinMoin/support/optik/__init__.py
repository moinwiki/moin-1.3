"""optik

A powerful, extensible, and easy-to-use command-line parser for Python.

By Greg Ward <gward@python.net>

See http://optik.sourceforge.net/
"""

# Copyright (c) 2001 Gregory P. Ward.  All rights reserved.
# See the README.txt distributed with Optik for licensing terms.

__revision__ = "$Id: __init__.py,v 1.2 2003/01/30 02:24:26 jhermann Exp $"

__version__ = "1.4"


# Re-import these for convenience
from MoinMoin.support.optik.option import Option
from MoinMoin.support.optik.option_parser import OptionGroup, OptionParser, Values, \
     SUPPRESS_HELP, SUPPRESS_USAGE, STD_HELP_OPTION
from MoinMoin.support.optik.help import \
     HelpFormatter, IndentedHelpFormatter, TitledHelpFormatter
from MoinMoin.support.optik.errors import OptionValueError


# Some day, there might be many Option classes.  As of Optik 1.3, the
# preferred way to instantiate Options is indirectly, via make_option(),
# which will become a factory function when there are many Option
# classes.
make_option = Option
