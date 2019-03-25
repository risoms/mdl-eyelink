#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 13 15:37:43 2019

@author: Semeon Risom
@email: semeon.risom@gmail.com.

Sample code to run SR Research Eyelink eyetracking system. Code is optimized for the Eyelink 1000 Plus (5.0),
but should be compatiable with earlier systems.
"""
import datetime
date = datetime.date.today().isoformat()

name = 'mdl-eyelink'
version = '%s'%(date)
.get_version()


author = 'Semeon Risom'
author_email = 'semeon.risom@gmail.com'
maintainer = 'Semeon Risom'
maintainer_email = 'semeon.risom@gmail.com'
url = 'https://semeon.io/d/mdl-eyelink'
description = 'mdl-eyelink: Bindings for Eyelink and Python.'
download_url = 'https://github.com/risoms/mdl-eyelink/'
long_description = open('README.md').read()
long_description_content_type = 'text/markdown'
license_ = open('LICENSE', 'r').read()
classifiers = [
    'Intended Audience :: Science/Research',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'License :: OSI Approved :: MIT License',
    'Topic :: Scientific/Engineering',
    'Topic :: Scientific/Engineering :: Visualization',
    'Topic :: Scientific/Engineering :: Human Machine Interfaces',
    'Topic :: Multimedia :: Graphics',
    'Operating System :: Unix',
    'Operating System :: MacOS',
    'Operating System :: Microsoft :: Windows'
]
install_requires = [
    'numpy',
    'scipy',
    'pandas',
    'psychopy',
    'win32api',
    'pyobjc'
]
packages = [
    'mdl',
    'mdl.eyetracking',
]
	
from setuptools import find_packages
try:
    from setuptools import setup
    is_setuptools = True
except ImportError:
    from distutils.core import setup

# Special handling for Anaconda / Miniconda
from setuptools.config import read_configuration
required = read_configuration('setup.cfg')['options']['install_requires']

if __name__ == "__main__":
    setup(
        name=name,
        version=version,
        author=author,
        author_email=author_email,
        maintainer=maintainer,
        maintainer_email=maintainer_email,	
        url=url,
        description=description,
        long_description = long_description,
		long_description_content_type = long_description_content_type,		
        download_url=download_url,
        classifiers=classifiers,	  				 
        license=license_,
        install_requires=install_requires,
		packages=packages,
    )