#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name='q3n',
    version='1.0.0',
    description='Quote Triple-Slash Notation — manage quoted text collections',

    author='Q3N Project',
    url='https://github.com/thuruht/q3n',
    packages=find_packages(include=['core', 'core.*', 'gui', 'gui.*']),
    python_requires='>=3.8',
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
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python :: 3',
        'Topic :: Text Processing :: General',
        'Topic :: Office/Business :: News/Database',
    ],
)
