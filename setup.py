#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Package installer

    @copyright: 2001-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""
__version__ = "$Revision: 1.32 $"[11:-2]

# Imports
import glob, os, string, sys

import distutils
from distutils.core import setup
from distutils.command.build_scripts import build_scripts

from MoinMoin.version import release, revision


#############################################################################
### Helper
#############################################################################

def trash_filter(f):
    file = os.path.basename(f)
    return file != 'CVS' and file[0] != '.'


#############################################################################
### Build script files
#############################################################################

class build_scripts_create(build_scripts):
    """ Overload the build_scripts command and create the scripts
        from scratch, depending on the target platform.

        You have to define the name of your package in an inherited
        class (due to the delayed instantiation of command classes
        in distutils, this cannot be passed to __init__).

        The scripts are created in an uniform scheme: they start the
        run() function in the module

            <packagename>.scripts.<mangled_scriptname>

        The mangling of script names replaces '-' and '/' characters
        with '-' and '.', so that they are valid module paths. 
    """
    package_name = None

    def copy_scripts(self):
        """ Create each script listed in 'self.scripts'
        """
        if not self.package_name:
            raise Exception("You have to inherit build_scripts_create and"
                " provide a package name")
        
        to_module = string.maketrans('-/', '_.')

        self.mkpath(self.build_dir)
        for script in self.scripts:
            outfile = os.path.join(self.build_dir, os.path.basename(script))

            #if not self.force and not newer(script, outfile):
            #    self.announce("not copying %s (up-to-date)" % script)
            #    continue

            if self.dry_run:
                self.announce("would create %s" % outfile)
                continue

            module = os.path.splitext(os.path.basename(script))[0]
            module = string.translate(module, to_module)
            script_vars = {
                'python': os.path.normpath(sys.executable),
                'package': self.package_name,
                'module': module,
            }

            self.announce("creating %s" % outfile)
            file = open(outfile, 'w')

            try:
                if sys.platform == "win32":
                    file.write('@echo off\n'
                        'if NOT "%%_4ver%%" == "" %(python)s -c "from %(package)s.scripts.%(module)s import run; run()" %%$\n'
                        'if     "%%_4ver%%" == "" %(python)s -c "from %(package)s.scripts.%(module)s import run; run()" %%*\n'
                        % script_vars)
                else:
                    file.write('#! %(python)s\n'
                        'from %(package)s.scripts.%(module)s import run\n'
                        'run()\n'
                        % script_vars)
            finally:
                file.close()
                os.chmod(outfile, 0755)


class build_scripts_moin(build_scripts_create):
    package_name = 'MoinMoin'


def scriptname(path):
    """ Helper for building a list of script names from a list of
        module files.
    """
    script = os.path.splitext(os.path.basename(path))[0]
    script = string.replace(script, '_', '-')
    if sys.platform == "win32":
        script = script + ".bat"
    return script

# build list of scripts from their implementation modules
moin_scripts = map(scriptname, glob.glob('MoinMoin/scripts/[!_]*.py'))


#############################################################################
### Call setup()
#############################################################################

setup_args = {
    'name': "moin",
    'version': release,
    'description': "MoinMoin %s.%s is a Python clone of WikiWiki" % (release, revision),
    'author': "Jürgen Hermann",
    'author_email': "jh@web.de",
    'url': "http://moinmoin.wikiwikiweb.de/",
    'license': "GNU GPL",
    'long_description': """
A WikiWikiWeb is a collaborative hypertext environment, with an
emphasis on easy access to and modification of information. MoinMoin
is a Python WikiClone that allows you to easily set up your own wiki,
only requiring a Python installation. 
""",
    'packages': [
        'MoinMoin',
        'MoinMoin.action',
        'MoinMoin.formatter',
        'MoinMoin.i18n',
        'MoinMoin.logfile',
        'MoinMoin.macro',
        'MoinMoin.parser',
        'MoinMoin.processor',
        'MoinMoin.scripts',
        'MoinMoin.scripts.accounts',
        'MoinMoin.scripts.xmlrpc-tools',
        'MoinMoin.stats',
        'MoinMoin.support',
        'MoinMoin.support.optik',
        'MoinMoin.theme',
        'MoinMoin.util',
        'MoinMoin.webapi',
        'MoinMoin.widget',
        'MoinMoin.wikixml',
        'MoinMoin.xmlrpc',

        # if we get *massive* amounts of test, this should probably be left out
        'MoinMoin._tests',
    ],

    # Override certain command classes with our own ones
    'cmdclass': {
        'build_scripts': build_scripts_moin,
    },

    'scripts': moin_scripts,

    'data_files': [
        ('share/moin/cgi-bin', filter(trash_filter, glob.glob('wiki/cgi-bin/*'))),
        ('share/moin/data', ['wiki/data/intermap.txt']),
        ('share/moin/data/text', filter(trash_filter, glob.glob('wiki/data/text/*'))),
        ('share/moin/data/plugin', ['wiki/data/plugin/__init__.py']),
        ('share/moin/data/plugin/action', ['wiki/data/plugin/action/__init__.py']),
        ('share/moin/data/plugin/macro', ['wiki/data/plugin/macro/__init__.py']),
        ('share/moin/data/plugin/formatter', ['wiki/data/plugin/formatter/__init__.py']),
        ('share/moin/data/plugin/parser', ['wiki/data/plugin/parser/__init__.py']),
        ('share/moin/data/plugin/processor', ['wiki/data/plugin/processor/__init__.py']),
        ('share/moin/data/plugin/theme', ['wiki/data/plugin/theme/__init__.py']),
        ('share/moin/data/plugin/xmlrpc', ['wiki/data/plugin/xmlrpc/__init__.py']),
        ('share/moin/data/user', ['wiki/data/user/README']),
        ('share/moin/htdocs', glob.glob('wiki/htdocs/*.html')),
        ('share/moin/htdocs/applets/TWikiDrawPlugin', glob.glob('wiki/htdocs/applets/TWikiDrawPlugin/*.jar')),
        ('share/moin/htdocs/classic/css', glob.glob('wiki/htdocs/classic/css/*.css')),
        ('share/moin/htdocs/classic/img', glob.glob('wiki/htdocs/classic/img/*.png')),
        ('share/moin/htdocs/starshine/css', glob.glob('wiki/htdocs/starshine/css/*.css')),
        ('share/moin/htdocs/starshine/img', glob.glob('wiki/htdocs/starshine/img/*.png')),
        ('share/moin/htdocs/viewonly/css',  glob.glob('wiki/htdocs/viewonly/css/*.css')),
        ('share/moin/htdocs/rightsidebar/css', glob.glob('wiki/htdocs/rightsidebar/css/*.css')),
        ('share/moin/htdocs/rightsidebar/img', glob.glob('wiki/htdocs/rightsidebar/img/*.png')),
        # viewonly has no own img/ yet
    ],
}

if hasattr(distutils.dist.DistributionMetadata, 'get_keywords'):
    setup_args['keywords'] = "wiki web"

if hasattr(distutils.dist.DistributionMetadata, 'get_platforms'):
    setup_args['platforms'] = "win32 posix"


try:
    apply(setup, (), setup_args)
except distutils.errors.DistutilsPlatformError, ex:
    print
    print str(ex)
    
    print """
POSSIBLE CAUSE

"distutils" often needs developer support installed to work
correctly, which is usually located in a separate package 
called "python%d.%d-dev(el)".

Please contact the system administrator to have it installed.
""" % sys.version_info[:2]
    sys.exit(1)

