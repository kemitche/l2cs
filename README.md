l2cs
====

## DEPRECATED

This project has been deprecated and will not be actively maintained. While Amazon Cloudsearch's
2011 API version did not support Lucene, the updated 2013 API revision natively supports Lucene
style queries and thus this library is not needed except for consumers who have yet to upgrade
to the new API version.

## Overview

`l2cs` - "lucene to CloudSearch" - is a module for converting search queries from [Apache lucene's base syntax](http://lucene.apache.org/core/3_6_0/queryparsersyntax.html) into an [Amazon CloudSearch boolean query](http://docs.amazonwebservices.com/cloudsearch/latest/developerguide/booleansearch.html).


Install
-------

Run `setup.py install` to install the module


Thanks
------

Many thanks to Matt Chaput, whose [whoosh module](https://bitbucket.org/mchaput/whoosh/overview) is a dependency and key component of `l2cs`.


License
-------

Please see `LICENSE.txt` in the source.
