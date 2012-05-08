#!/usr/bin/env python

import unittest

import l2cs


class l2csTester(unittest.TestCase):
    def setUp(self):
        self.parser = l2cs.make_parser(int_fields=["count", "number"],
                                       yesno_fields=["active", "ready"])
    
    def tearDown(self):
        self.parser = None
    
    def _run_test(self, input_, expected):
        parsed = self.parser.parse(input_)
        pieces = l2cs.walk_clause(parsed)
        result = ''.join(pieces)
        errmsg = ("\ninput: %s\nparsed: %s\nresult: %s\nexpected: %s" %
                  (input_, parsed, result, expected))
        self.assertEqual(result, expected, errmsg)
    
    # basic fields
    def test_fields1(self):
        self._run_test("foo", "(field text 'foo')")
    def test_fields2(self):
        self._run_test("foo:bar", "(field foo 'bar')")
    
    # phrases
    def test_phrases1(self):
        self._run_test('"foo bar baz"', "(field text 'foo bar baz')")
    
    # AND clauses
    def test_and1(self):
        self._run_test("foo AND bar", "(and (field text 'foo') (field text 'bar'))")
    def test_and2(self):
        self._run_test("foo AND bar:baz", "(and (field text 'foo') (field bar 'baz'))")
    
    # OR clauses
    def test_or1(self):
        self._run_test("foo OR bar", "(or (field text 'foo') (field text 'bar'))")
    def test_or2(self):
        self._run_test("bar:baz OR foo", "(or (field bar 'baz') (field text 'foo'))")
    
    # NOT clauses
    def test_not1(self):
        self._run_test("NOT foo", "(not (field text 'foo'))")
    def test_not2(self):
        self._run_test("baz NOT bar", "(or (field text 'baz') (not (field text 'bar')))")
    def test_not3(self):
        self._run_test("foo:bar NOT foo:baz", "(or (field foo 'bar') (not (field foo 'baz')))")
    def test_not4(self):
        self._run_test("bar AND foo:-baz", "(and (field text 'bar') (not (field text 'baz')))")
    
    # quotes
    def test_quote1(self):
        self._run_test("hello:\"goodbye you're sir\"", "(field hello 'goodbye you\\'re sir')")
    def test_quote2(self):
        self._run_test("hello:\"goodbye you''re sir\"", "(field hello 'goodbye you\\'\\'re sir')")
    
    # int fields
    def test_int1(self):
        self._run_test("count:12", "count:12")
    def test_int2(self):
        self._run_test("count:foo number:12 foo:bar", "(or number:12 (field foo 'bar'))")
    
    # yes/no fields
    def test_yesno1(self):
        self._run_test("ready:yes active:n", "(or ready:1 active:0)")
    
    # prefixes
    def test_prefix1(self):
        self._run_test("foo:bar*", "(field foo 'bar*')")


if __name__ == '__main__':
    unittest.main()