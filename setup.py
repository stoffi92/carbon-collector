# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

setup(
    name='carboncollector',
    version='0.0.1b',
    description='Multiprocessor collector for carbon db',
    long_description=readme,
    author='Christoph Loibl',
    author_email='cl@tix.at',
    packages=find_packages(exclude=('tests', 'docs')),
    entry_points={
        'console_scripts': ['ccollector=carboncollector.collector_app:main'],
    },
    install_requires=[
        'easysnmp', 'requests'
    ],

)

