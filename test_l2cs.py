#!/usr/bin/env python

import unittest

import l2cs

TESTS = [
         # basic fields
         ("foo", "(field text 'foo')"),
         ("foo:bar", "(field foo 'bar')"),
         
         # phrases
         ('"foo bar baz"', "(field text 'foo bar baz')"),
         
         # AND clauses
         ("foo AND bar", "(and (field text 'foo') (field text 'bar'))"),
         ("foo AND bar:baz", "(and (field text 'foo') (field bar 'baz'))"),
         
         # OR clauses
         ("foo OR bar", "(or (field text 'foo') (field text 'bar'))"),
         ("bar:baz OR foo", "(or (field bar 'baz') (field text 'foo'))"),
         
         # NOT clauses
         ("NOT foo", "(not (field text 'foo'))"),
         ("baz NOT bar", "(and (field text 'baz') (not (field text 'bar')))"),
         ("foo:bar NOT foo:baz", "(and (field foo 'bar') (not (field foo 'baz')))"),
         ("bar AND foo:-baz", ),
         
         # quotes
         ("hello:goodbye you're sir", "(field hello 'goodbye you\'re sir')"),
         ("hello:goodbye you''re sir", "(field hello 'goodbye you\'\'re sir')"),
         
         # int fields
         ("count:12", "count:1"),
         ("count:foo number:12 foo:bar", "(or number:12 (field foo 'bar'))"),
         
         # yes/no fields
         ("is_ready:yes is_active:n", "(or is_ready:1 is_active:0)"),
         ]


def run_tests():
    '''because why bother with the stdlib testing library, anyway?'''
    for input_, output in TESTS:
        print input_, 'becomes', output, "? ... "
        result = l2cs.convert(input_, int_fields=["count", "number"],
                              yesno_fields=["is_active", "is_ready"])
        try:
            assert result == output
        except AssertionError:
            print "\tnope:", result, "!=", output
            raise
        print "\tyup!"