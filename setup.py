# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

setup(
    name='carboncollector',
    version='0.0.1',
    description='Multiprocessor collector for carbon db',
    long_description=readme,
    author='Christoph Loibl',
    author_email='cl@tix.at',
    packages=find_packages(exclude=('tests', 'docs')),
    entry_points={
        'console_scripts': ['ccollector=carboncollector.collector_app:main',
                            'tagcollector=carboncollector.tagcollector_app:main'],
    },
    install_requires=[
        'easysnmp', 'requests'
    ],

)
