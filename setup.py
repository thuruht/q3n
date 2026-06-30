#!/usr/bin/env python3
from setuptools import setup, find_packages
from core import __version__

setup(
    name='q3n',
    version=__version__,
    description='Quote Triple-Slash Notation — manage quoted text collections',
    author='Q3N Project',
    url='https://github.com/thuruht/q3n',
    license='AGPL-3.0-only',
    packages=find_packages(include=['core', 'core.*', 'gui', 'gui.*']),
    package_data={'gui': ['*.qss']},
    python_requires='>=3.9',
    install_requires=[
        'PySide6>=6.5',
    ],
    scripts=[
        'tools/q3n',
        'bin/q3n-gui',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Text Processing :: General',
        'Topic :: Office/Business :: News/Database',
    ],
)
