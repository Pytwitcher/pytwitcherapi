#!/usr/bin/env python

from __future__ import print_function
from setuptools import setup
from setuptools import find_packages
from setuptools.command.test import test as TestCommand
import io
import os
import sys


here = os.path.abspath(os.path.dirname(__file__))


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


class Tox(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import tox
        errcode = tox.cmdline(self.test_args)
        sys.exit(errcode)


long_description = read('README.rst', 'HISTORY.rst')
install_requires = ['requests', 'requests-oauthlib', 'oauthlib', 'm3u8']
tests_require = ['tox']


setup(
    name='pytwitcherapi',
    version='0.3.0',
    description='Python API for interacting with twitch.tv',
    long_description=long_description,
    author='David Zuber',
    author_email='zuber.david@gmx.de',
    url='https://github.com/Pytwitcher/pytwitcherapi',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    package_data={'pytwitcherapi': ['html/*.html']},
    include_package_data=True,
    tests_require=tests_require,
    install_requires=install_requires,
    cmdclass={'test': Tox},
    license='BSD',
    zip_safe=False,
    keywords='pytwitcherapi',
    test_suite='pytwitcherapi.test.pytwitcherapi',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Operating System :: OS Independent',
    ],
)
