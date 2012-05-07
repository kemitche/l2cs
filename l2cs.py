#!/usr/bin/env python

import sys

import whoosh.qparser
import whoosh.qparser.plugins
import whoosh.query


HANDLERS = {}


def handler(classes):
    def decorator(fn):
        for cls in classes:
            if cls in HANDLERS:
                raise ValueError("%s already has a handler")
            HANDLERS[cls] = fn
        return fn
    return decorator


@handler((whoosh.query.Term,))
def build_field(clause):
    yield "(field "
    yield clause.fieldname
    yield " '"
    yield clause.text
    yield "')"


@handler((whoosh.query.And, whoosh.query.Or))
def build_grouper(clause):
    yield "("
    yield clause.__class__.__name__.lower()
    for child_clause in clause.children():
        yield " "
        for piece in walk_clause(child_clause):
            yield piece
    yield ")"


def walk_clause(clause):
    handler_fn = HANDLERS[clause.__class__]
    for piece in handler_fn(clause):
        yield piece


def parse_string(query):
    parser = whoosh.qparser.QueryParser('text', None)
    parser.add_plugin(whoosh.qparser.plugins.PlusMinusPlugin())
    return parser.parse(query)


def convert(query):
    parsed = parse_string(query)
    pieces = walk_clause(parsed)
    return ''.join(pieces)


TESTS = [
         # basic fields
         ("foo", "(field text 'foo')"),
         ("foo:bar", "(field foo 'bar'"),
         # AND clauses
         ("foo AND bar", "(and (field text 'foo') (field text 'bar'))"),
         ("foo AND bar:baz", "(and (field text 'foo') (field bar 'baz'))"),
         # OR clauses
         ("foo OR bar", "(or (field text 'foo') (field text 'bar'))"),
         ("bar:baz OR foo", "(or (field bar 'baz') (field text 'foo'))"),
         ]


def run_tests():
    for input_, output in TESTS:
        assert convert(input_) == output


def main(args):
    '''For command line testing'''
    query = ' '.join(args[1:])
    print "Lucene query:", query
    parsed = parse_string(query)
    print "Parsed representation:", repr(parsed)
    cloudsearch_query = ''.join(walk_clause(parsed))
    print "Cloudsearch form:", cloudsearch_query


if __name__ == '__main__':
    main(sys.argv)
