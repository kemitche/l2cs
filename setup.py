#!/usr/bin/env python2.7

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='l2cs',
    version="0.1.0",
    author='Keith Mitchell',
    author_email='kemitche@reddit.com',
    description=("Rewrites queries from lucene syntax to"
                 "Amazon Cloudsearch syntax"),
    license='BSD',
    url="http://github.com/kemitche/l2cs",
    install_requires=["whoosh"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
)
