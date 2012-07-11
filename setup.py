#!/usr/bin/env python2.7

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

import l2cs
version = l2cs.__version__

setup(
    name='l2cs',
    version=version,
    author='Keith Mitchell',
    author_email='kemitche@reddit.com',
    description=("Rewrites queries from lucene syntax to"
                 " Amazon Cloudsearch syntax"),
    license='BSD',
    url="http://github.com/kemitche/l2cs",
    download_url="http://github.com/kemitche/l2cs/tarball/v%(ver)s#egg=l2cs-%(ver)s" % {'ver': version},
    install_requires=["whoosh>=2.3"],
    py_modules=['l2cs'],
    include_package_data=True,
    test_suite="test_l2cs",

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
