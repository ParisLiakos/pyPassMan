#!/usr/bin/env python3

from setuptools import setup

setup(
    name='pyPassMan',
    version='0.1',
    description='GTK3 password manager.',
    author='Paris Liakos',
    author_email='rootatwc@gmail.com',
    url='http://github.com/ParisLiakos/pyPassMan',
    packages=['pyPassMan'],
    requires=['gi', 'Crypto'],
    data_files=[
        ('/usr/local/share/applications', ['pyPassMan.desktop'])
    ],
    entry_points={
        'console_scripts': [
            'pyPassManGtk3=pyPassMan.gtk3:main',
        ]
    },
)
