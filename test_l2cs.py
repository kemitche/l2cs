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
        self.schema = l2cs.make_schema(["foo", "bar", "baz", "count", "number",
                                        "active", "text", "ready", "active",
                                        "alias", "alias1", "alias2"],
                                       ["timestamp", "date"])
        self.schema_parser = l2cs.make_parser(int_fields=["count", "number"],
                                              yesno_fields=["active", "ready"],
                                              aliases={"alias": ["alias1",
                                                                 "alias2"]},
                                              schema=self.schema)
    
    def tearDown(self):
        self.parser = None
        self.schema = None
        self.schema_parser = None
    
    def _run_test(self, input_, expected, parser=None):
        parser = parser or self.parser
        parsed = parser.parse(input_, debug=DEBUG)
        pieces = l2cs.walk_clause(parsed)
        result = u''.join(pieces)
        errmsg = ("\ninput: %s\nparsed: %r\nresult: %s\nexpected: %s" %
                  (input_, parsed, result, expected))
        self.assertEqual(result, expected, errmsg)
    
    # basic fields
    def test_fields1(self):
        self._run_test(u"foo", u"(field text 'foo')")
    def test_fields2(self):
        self._run_test(u"foo:bar", u"(field foo 'bar')")
    
    # phrases
    def test_phrases1(self):
        self._run_test(u'"foo bar baz"', u"(field text 'foo bar baz')")
    
    # AND clauses
    def test_and1(self):
        self._run_test(u"foo AND bar", u"(and (field text 'foo') (field text 'bar'))")
    def test_and2(self):
        self._run_test(u"foo AND bar:baz", u"(and (field text 'foo') (field bar 'baz'))")
    
    # OR clauses
    def test_or1(self):
        self._run_test(u"foo OR bar", u"(or (field text 'foo') (field text 'bar'))")
    def test_or2(self):
        self._run_test(u"bar:baz OR foo", u"(or (field bar 'baz') (field text 'foo'))")
    
    # NOT clauses
    def test_not1(self):
        self._run_test(u"NOT foo", u"(not (field text 'foo'))")
    def test_not2(self):
        self._run_test(u"baz NOT bar", u"(and (field text 'baz') (not (field text 'bar')))")
    def test_not3(self):
        self._run_test(u"foo:bar NOT foo:baz", u"(and (field foo 'bar') (not (field foo 'baz')))")
    def test_not4(self):
        self._run_test(u"bar AND foo:-baz", u"(and (field text 'bar') (not (field text 'baz')))")
    def test_not5(self):
        '''Stray hyphens at the end should not count as NOTs'''
        self._run_test(u"foo:bar -", u"(and (field foo 'bar') (field text '-'))")
    def test_not6(self):
        '''Stray hyphens at the end should not NOT, even with spaces'''
        self._run_test(u"foo:bar -  ", u"(and (field foo 'bar') (field text '-'))")
    def test_not7(self):
        '''Duplicate hyphens should be smooshed into one not clause'''
        self._run_test(u"test --foo", u"(and (field text 'test') (not (field text 'foo')))")
    def test_not8(self):
        '''Duplicate hyphens hanging around in the middle of nowhere'''
        self._run_test(u"test -- foo", u"(and (field text 'test') (field text '--') (field text 'foo'))")
    def test_not9(self):
        '''Duplicate hyphens, spaced out'''
        self._run_test(u"test - - foo", u"(and (field text 'test') (field text '-') (field text 'foo'))")
    
    # quotes
    def test_quote1(self):
        self._run_test(u"hello:\"goodbye you're sir\"", u"(field hello 'goodbye you\\'re sir')")
    def test_quote2(self):
        self._run_test(u"hello:\"goodbye you''re sir\"", u"(field hello 'goodbye you\\'\\'re sir')")
    
    # int fields
    def test_int1(self):
        self._run_test(u"count:12", u"count:12")
    def test_int2(self):
        self._run_test(u"count:foo number:12 foo:bar", u"(and number:12 (field foo 'bar'))")
    
    # yes/no fields
    def test_yesno1(self):
        self._run_test(u"ready:yes active:n", u"(and ready:1 active:0)")
    
    # prefixes
    def test_prefix1(self):
        self._run_test(u"foo:bar*", u"(field foo 'bar*')")
    
    # Aliases
    def test_alias1(self):
        self._run_test(u"alias1:foo", u"(field alias 'foo')")
    def test_alias2(self):
        '''Make sure that referencing the base of the alias still works'''
        self._run_test(u"alias:foo", u"(field alias 'foo')")
    
    # NullQueries
    def test_null1(self):
        self._run_test(u'""', u'')
    def test_null2(self):
        self._run_test(u'foo:""', u'')
    def test_null3(self):
        self._run_test(u'foo:"" bar:baz', u"(field bar 'baz')")
    
    # Schema
    def test_schema1(self):
        self._run_test(u"foo:bar", u"(field foo 'bar')", self.schema_parser)
    def test_schema2(self):
        self._run_test(u"foo:bar notfoo:something", u"(and (field foo 'bar') (field text 'notfoo') (field text 'something'))", self.schema_parser)
    
    # Unicode checks
    def test_unicode1(self):
        '''Non-unicode ASCII input should raise AssertionError'''
        self.assertRaises(AssertionError, self._run_test, 'foo:bar', u"(field foo 'bar')")
    def test_unicode2(self):
        '''Non-unicode UTF-8 input should raise AssertionError'''
        self.assertRaises(AssertionError, self._run_test, 'foo:\xe0\xb2\xa0_\xe0\xb2\xa0', u"(field foo '\u0ca0_\u0ca0')")
    def test_unicode4(self):
        '''Result of l2cs.convert should be unicode'''
        result = l2cs.convert(u'foo:bar', self.parser)
        self.assertIsInstance(result, unicode)
    def test_unicode3(self):
        '''Result of l2cs.convert should be unicode, part 2'''
        result = l2cs.convert(u'foo:\u0ca0_\u0ca0', self.parser)
        self.assertIsInstance(result, unicode)
    
    ### Test cases from resolved issues ###
    # The remaining test cases protect against issues that have been resolved
    
    # Unsupported "+" syntax gets ignored, AndMaybe clauses are avoided
    def test_plus1(self):
        self._run_test(u"learn c++ programming", u"(and (field text 'learn') (field text 'c++') (field text 'programming'))")
    def test_plus2(self):
        self._run_test(u"learn c++", u"(and (field text 'learn') (field text 'c++'))")
    
    def test_minus_in_parentheses(self):
        self._run_test(u"text:baz AND url:(-foo AND bar)", u"(and (field text 'baz') (not (field url 'foo')) (field url 'bar'))")
    
    def test_minus_midword(self):
        self._run_test(u"baz:foo-bar", u"(field baz 'foo-bar')")
    
    def test_unicode_intnodes1(self):
        '''Clauses with integers should work with schemas
        As reported in https://github.com/kemitche/l2cs/issues/18
        
        '''
        try:
            self._run_test(u"count:1", u"count:1", self.schema_parser)
        except AssertionError as e:
            self.fail(e)


if __name__ == '__main__':
    unittest.main()
