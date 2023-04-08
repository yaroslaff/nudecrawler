#!/usr/bin/env python3

from setuptools import setup
import os
import sys

from importlib.machinery import SourceFileLoader

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def get_version(path):
    foo = SourceFileLoader(os.path.basename(path),"nudecrawler/version.py").load_module()
    return foo.version

setup(
    name='nudecrawler',
    version=get_version('bin/nudecrawler'),
    packages=['nudecrawler'],
    scripts=[
    'bin/nudecrawler', 
    'bin/detect-image-aid.py',
    'bin/detect-image-nsfw-api.py',
    'bin/detect-image-nudenet.py',
    'bin/detect-server-nudenet.py',
    'bin/refresh-nsfw-api.sh'
    ],

    install_requires=['bs4', 'requests', 'pillow', 'nudepy', 'transliterate' ,'evalidate', 'python-dotenv'],

    url='https://github.com/yaroslaff/nudecrawler',
    license='MIT',
    author='Yaroslav Polyakov',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    author_email='yaroslaff@gmail.com',
    description='Crawl telegra.ph for nude pictures and videos',
    python_requires='>=3.9',
    extras_require={
        'nudenet': ["flask", "nudenet", "python-daemon"],
    },

    classifiers=[
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',

        # Pick your license as you wish (should match "license" above)
         'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.6',
    ],
)
