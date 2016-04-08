#! /usr/bin/env python

"""
    MoinMoin - Package installer

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: setup.py,v 1.15 2002/02/07 01:03:32 jhermann Exp $
"""
__version__ = "$Revision: 1.15 $"[11:-2]

# Imports
import glob, os, string, sys
import distutils
from distutils.core import setup
from distutils.command.build_scripts import build_scripts
from MoinMoin.version import release, revision


#############################################################################
### Helper
#############################################################################

def pagefile_filter(f):
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
                        '%(python)s -c "from %(package)s.scripts.%(module)s import run; run()" %%$\n'
                        % script_vars)
                else:
                    file.write('#! %(python)s\n'
                        'from %(package)s.scripts.%(module)s import run\n'
                        'run()\n'
                        % script_vars)
            finally:
                file.close()


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
    'url': "http://moin.sf.net/",
    'licence': "GNU GPL",
    'long_description': """
A WikiWikiWeb is a collaborative hypertext environment, with an
emphasis on easy access to and modification of information. MoinMoin
is a Python WikiClone that allows you to easily set up your own wiki,
only requiring a Web server and a Python installation. 
""",
    'packages': [
        'MoinMoin',
        'MoinMoin.action',
        'MoinMoin.formatter',
        'MoinMoin.i18n',
        'MoinMoin.macro',
        'MoinMoin.parser',
        'MoinMoin.py15',
        'MoinMoin.scripts',
        'MoinMoin.stats',
        'MoinMoin.support',
        'MoinMoin.twisted',
        'MoinMoin.webapi',
        'MoinMoin.wikixml',
    ],

    # Override certain command classes with our own ones
    'cmdclass': {
        'build_scripts': build_scripts_moin,
    },

    'scripts': moin_scripts,

    'data_files': [
        ('share/moin/cgi-bin',
            glob.glob('wiki/cgi-bin/*.cgi') +
            glob.glob('wiki/cgi-bin/*.py')  ),
        ('share/moin/data',
            ['wiki/data/intermap.txt']),
        ('share/moin/data/text',
            filter(pagefile_filter, glob.glob('wiki/data/text/*'))),
        ('share/moin/data/backup', []),
        ('share/moin/data/cache', []),
        ('share/moin/data/pages', []),
        ('share/moin/data/plugin', []),
        ('share/moin/data/plugin/action', []),
        ('share/moin/data/plugin/macro', []),
        ('share/moin/data/user', []),
        ('share/moin/htdocs',
            glob.glob('wiki/htdocs/*.html')),
        ('share/moin/htdocs/css',
            glob.glob('wiki/htdocs/css/*.css')),
        ('share/moin/htdocs/img',
            glob.glob('wiki/htdocs/img/*.gif') +
            glob.glob('wiki/htdocs/img/*.png')),
        ('share/moin/htdocs/applets/TWikiDrawPlugin',
            glob.glob('wiki/htdocs/applets/TWikiDrawPlugin/*.jar')),
    ],
}

if hasattr(distutils.dist.DistributionMetadata, 'get_keywords'):
    setup_args['keywords'] = "wiki web"

if hasattr(distutils.dist.DistributionMetadata, 'get_platforms'):
    setup_args['platforms'] = "win32 posix"

apply(setup, (), setup_args)

