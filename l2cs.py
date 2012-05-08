#!/usr/bin/env python
'''
Need handlers for:
Prefix

Need magic for:
dates/datewords to timestamps?

Need to restrict out (sanely):
Wildcards (non-prefix)

Add support for pushing schema into place, to allow pre-fixing "bad" fields

'''

import sys

import whoosh.qparser
import whoosh.qparser.plugins
import whoosh.qparser.syntax
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


@handler((whoosh.query.Term, whoosh.query.Phrase, whoosh.query.Prefix))
def build_field(clause):
    integer_field = getattr(clause, "integer_field", False)
    if not integer_field:
        yield "(field "
        yield clause.fieldname
        yield " '"
        if isinstance(clause, whoosh.query.Term):
            yield clause.text.replace(r"'", r"\'")
        elif isinstance(clause, whoosh.query.Prefix):
            yield clause.text.replace(r"'", r"\'")
            yield '*'
        elif isinstance(clause, whoosh.query.Phrase):
            for word in clause.words[:-1]:
                yield word.replace(r"'", r"\'")
                yield " "
            yield clause.words[-1]
        yield "')"
    else:
        yield clause.fieldname
        yield ':'
        yield clause.text


@handler((whoosh.query.And, whoosh.query.Or, whoosh.query.Not))
def build_grouper(clause):
    yield "("
    yield clause.__class__.__name__.lower()
    for child_clause in clause.children():
        yield " "
        for piece in walk_clause(child_clause):
            yield piece
    yield ")"


@handler((whoosh.query.AndNot,))
def build_compound(clause):
    yield '(and '
    use, avoid = list(clause.children())
    for piece in walk_clause(use):
        yield piece
    yield ' (not '
    for piece in walk_clause(avoid):
        yield piece
    yield '))'


def walk_clause(clause):
    handler_fn = HANDLERS[clause.__class__]
    for piece in handler_fn(clause):
        yield piece


class IntNode(whoosh.qparser.syntax.WordNode):
    def __init__(self, value):
        self.__int_value = int(value)
        whoosh.qparser.syntax.WordNode.__init__(self, str(self.__int_value))
    
    def query(self, parser):
        q = whoosh.qparser.syntax.WordNode.query(self, parser)
        q.integer_field = True
        return q


class IntNodePlugin(whoosh.qparser.plugins.PseudoFieldPlugin):
    def __init__(self, fieldnames):
        mapping = {}
        for name in fieldnames:
            function = self.modify_node_fn(name, self.modify_node)
            mapping[name] = function
        super(IntNodePlugin, self).__init__(mapping)
    
    @staticmethod
    def modify_node_fn(fname, base_fn):
        def fn(node):
            return base_fn(fname, node)
        return fn
    
    @staticmethod
    def modify_node(fieldname, node):
        if node.has_text:
            try:
                new_node = IntNode(node.text)
                new_node.set_fieldname(fieldname)
                return new_node
            except ValueError:
                return None
        else:
            return node


class YesNoPlugin(IntNodePlugin):
    @staticmethod
    def modify_node(fieldname, node):
        if node.has_text:
            if node.text in ("yes", "y", "1"):
                new_node = IntNode(1)
            else:
                new_node = IntNode(0)
            new_node.set_fieldname(fieldname)
            return new_node
        else:
            return node


DEFAULT_PLUGINS = (
                   whoosh.qparser.plugins.WhitespacePlugin(),
                   whoosh.qparser.plugins.SingleQuotePlugin(),
                   whoosh.qparser.plugins.FieldsPlugin(),
                   whoosh.qparser.plugins.PhrasePlugin(),
                   whoosh.qparser.plugins.PrefixPlugin(),
                   whoosh.qparser.plugins.GroupPlugin(),
                   whoosh.qparser.plugins.OperatorsPlugin(AndMaybe=None,
                                                          Require=None),
                   whoosh.qparser.plugins.EveryPlugin(),
                   whoosh.qparser.plugins.PlusMinusPlugin(),
                   )


def make_parser(default_field='text', plugins=DEFAULT_PLUGINS, schema=None,
                int_fields=None, yesno_fields=None):
    parser = whoosh.qparser.QueryParser(default_field, schema, plugins=plugins)
    if int_fields:
        parser.add_plugin(IntNodePlugin(int_fields))
    if yesno_fields:
        parser.add_plugin(YesNoPlugin(yesno_fields))
    return parser


def convert(query, **kw):
    parser = make_parser(**kw)
    parsed = parser.parse(query)
    pieces = walk_clause(parsed)
    return ''.join(pieces)


def main(args):
    '''For command line experimentation'''
    query = ' '.join(args[1:])
    print "Lucene input:", query
    parser = make_parser(int_fields=["count", "number"],
                         yesno_fields=["active", "ready"])
    parsed = parser.parse(query)
    print "Parsed representation:", repr(parsed)
    print "Lucene form:", str(parsed)
    cloudsearch_query = ''.join(walk_clause(parsed))
    print "Cloudsearch form:", cloudsearch_query


if __name__ == '__main__':
    main(sys.argv)
