#!/usr/bin/env python

import os
import unittest

import l2cs

DEBUG = bool(os.environ.get("L2CSDEBUG", ""))


class l2csTester(unittest.TestCase):
    def setUp(self):
        self.parser = l2cs.make_parser(int_fields=["count", "number"],
                                       yesno_fields=["active", "ready"],
                                       aliases={"alias": ["alias1", "alias2"]})
    
    def tearDown(self):
        self.parser = None
    
    def _run_test(self, input_, expected, parser=None):
        parser = parser or self.parser
        parsed = parser.parse(input_, debug=DEBUG)
        pieces = l2cs.walk_clause(parsed)
        result = ''.join(pieces)
        errmsg = ("\ninput: %s\nparsed: %r\nresult: %s\nexpected: %s" %
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
        self._run_test("baz NOT bar", "(and (field text 'baz') (not (field text 'bar')))")
    def test_not3(self):
        self._run_test("foo:bar NOT foo:baz", "(and (field foo 'bar') (not (field foo 'baz')))")
    def test_not4(self):
        self._run_test("bar AND foo:-baz", "(and (field text 'bar') (not (field text 'baz')))")
    def test_not5(self):
        '''Stray hyphens at the end should not count as NOTs'''
        self._run_test("foo:bar -", "(and (field foo 'bar') (field text '-'))")
    def test_not6(self):
        '''Stray hyphens at the end should not NOT, even with spaces'''
        self._run_test("foo:bar -  ", "(and (field foo 'bar') (field text '-'))")
    def test_not7(self):
        '''Duplicate hyphens should be smooshed into one not clause'''
        self._run_test("test --foo", "(and (field text 'test') (not (field text 'foo')))")
    def test_not8(self):
        '''Duplicate hyphens hanging around in the middle of nowhere'''
        self._run_test("test -- foo", "(and (field text 'test') (field text '--') (field text 'foo'))")
    def test_not9(self):
        '''Duplicate hyphens, spaced out'''
        self._run_test("test - - foo", "(and (field text 'test') (field text '-') (field text 'foo'))")
    
    # quotes
    def test_quote1(self):
        self._run_test("hello:\"goodbye you're sir\"", "(field hello 'goodbye you\\'re sir')")
    def test_quote2(self):
        self._run_test("hello:\"goodbye you''re sir\"", "(field hello 'goodbye you\\'\\'re sir')")
    
    # int fields
    def test_int1(self):
        self._run_test("count:12", "count:12")
    def test_int2(self):
        self._run_test("count:foo number:12 foo:bar", "(and number:12 (field foo 'bar'))")
    
    # yes/no fields
    def test_yesno1(self):
        self._run_test("ready:yes active:n", "(and ready:1 active:0)")
    
    # prefixes
    def test_prefix1(self):
        self._run_test("foo:bar*", "(field foo 'bar*')")
    
    # Aliases
    def test_alias1(self):
        self._run_test("alias1:foo", "(field alias 'foo')")
    def test_alias2(self):
        '''Make sure that referencing the base of the alias still works'''
        self._run_test("alias:foo", "(field alias 'foo')")
    
    # NullQueries
    def test_null1(self):
        self._run_test('""', '')
    def test_null2(self):
        self._run_test('foo:""', '')
    def test_null3(self):
        self._run_test('foo:"" bar:baz', "(field bar 'baz')")
    
    ### Test cases from resolved issues ###
    # The remaining test cases protect against issues that have been resolved
    
    # Unsupported "+" syntax gets ignored, AndMaybe clauses are avoided
    def test_plus1(self):
        self._run_test("learn c++ programming", "(and (field text 'learn') (field text 'c++') (field text 'programming'))")
    def test_plus2(self):
        self._run_test("learn c++", "(and (field text 'learn') (field text 'c++'))")
    
    def test_minus_in_parentheses(self):
        self._run_test("text:baz AND url:(-foo AND bar)", "(and (field text 'baz') (not (field url 'foo')) (field url 'bar'))")
    
    def test_minus_midword(self):
        self._run_test("baz:foo-bar", "(field baz 'foo-bar')")


if __name__ == '__main__':
    unittest.main()
