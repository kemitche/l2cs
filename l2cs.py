#!/usr/bin/env python
'''
l2cs (lucene to CloudSearch) - is a module for converting search queries
from Apache lucene's base syntax
(http://lucene.apache.org/core/3_6_0/queryparsersyntax.html)
into an Amazon CloudSearch boolean query
(http://docs.amazonwebservices.com/cloudsearch/latest/developerguide/booleansearch.html).
'''

import sys

import whoosh.fields
import whoosh.qparser.default
import whoosh.qparser.plugins
import whoosh.qparser.syntax
import whoosh.qparser.taggers
import whoosh.query


__version__ = "2.0.0"


HANDLERS = {}


def handler(*classes):
    def decorator(fn):
        for cls in classes:
            if cls in HANDLERS:
                raise ValueError("%s already has a handler")
            HANDLERS[cls] = fn
        return fn
    return decorator


# NullQuery is an instance of _NullQuery class
@handler(whoosh.query.NullQuery.__class__)
def build_null(clause):
    yield ""


@handler(whoosh.query.Term, whoosh.query.Phrase, whoosh.query.Prefix)
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


@handler(whoosh.query.And, whoosh.query.Or, whoosh.query.Not,
         whoosh.query.AndMaybe)
def build_grouper(clause):
    yield "("
    # CloudSearch only supports 'and' and 'or' clauses; neither really fit
    # with the concept of "AndMaybe", which tries to "boost" results that
    # include the "Maybe" portion of the clause.
    if isinstance(clause, whoosh.query.AndMaybe):
        yield "and"
    else:
        yield clause.__class__.__name__.lower()
    for child_clause in clause.children():
        yield " "
        for piece in walk_clause(child_clause):
            yield piece
    yield ")"


@handler(whoosh.query.AndNot)
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


class PseudoFieldPlugin(whoosh.qparser.plugins.PseudoFieldPlugin):
    def __init__(self, fieldnames):
        mapping = {}
        for name in fieldnames:
            function = self.modify_node_fn(name, self.modify_node)
            mapping[name] = function
        super(PseudoFieldPlugin, self).__init__(mapping)
    
    @staticmethod
    def modify_node_fn(fname, base_fn):
        def fn(node):
            return base_fn(fname, node)
        return fn
    
    def modify_node(self, fieldname, node):
        raise NotImplementedError


class IntNodePlugin(PseudoFieldPlugin):
    def modify_node(self, fieldname, node):
        if node.has_text:
            try:
                new_node = IntNode(node.text)
                new_node.set_fieldname(fieldname)
                return new_node
            except ValueError:
                return None
        else:
            return node


class YesNoPlugin(PseudoFieldPlugin):
    def modify_node(self, fieldname, node):
        if node.has_text:
            if node.text in ("yes", "y", "1"):
                new_node = IntNode(1)
            else:
                new_node = IntNode(0)
            new_node.set_fieldname(fieldname)
            return new_node
        else:
            return node


class FieldAliasPlugin(PseudoFieldPlugin):
    def __init__(self, aliases):
        reverse_aliases = {}
        for fieldname, alias_list in aliases.items():
            for alias in alias_list:
                reverse_aliases[alias] = fieldname
        self.aliases = reverse_aliases
        super(FieldAliasPlugin, self).__init__(self.aliases.keys())
    
    def modify_node(self, fieldname, node):
        if node.has_text:
            node.set_fieldname(self.aliases[fieldname])
        return node


class MinusPlugin(whoosh.qparser.plugins.Plugin):
    '''This differs from whoosh's PlusMinusPlugin. The concept of "AndMaybe"
    isn't one that applies to CloudSearch, so "+" actions aren't needed.
    Additionally, the logic is simplified from the whoosh version to just
    swap out the nodes
    '''
    class Minus(whoosh.qparser.syntax.MarkerNode):
        pass
    
    def __init__(self, minusexpr=r"(?=\B)-+(?=\w)"):
        self.minusexpr = minusexpr

    def taggers(self, parser):
        minus_tagger = whoosh.qparser.taggers.FnTagger(self.minusexpr,
                                                       self.Minus)
        return [(minus_tagger, 0)]
    
    def filters(self, parser):
        return [(self.do_minus, 505)]
    
    def do_minus(self, parser, group):
        '''This filter sorts nodes in a flat group into "required", "default",
        and "banned" subgroups based on the presence of plus and minus nodes.
        '''
        grouper = group.__class__()
        
        next_not = None
        for node in group:
            if isinstance(node, self.Minus):
                if next_not is not None:
                    # Two Minuses in a row; skip the second one
                    continue
                next_not = whoosh.qparser.syntax.NotGroup()
                grouper.append(next_not)
            else:
                # Nodes with children: search for nested Minus nodes
                if isinstance(node, whoosh.qparser.syntax.GroupNode):
                    node = self.do_minus(parser, node)
                if next_not is not None:
                    next_not.append(node)
                    next_not = None
                else:
                    grouper.append(node)
        if next_not is not None:
            # Remove the empty NotGroup
            grouper.pop()
        
        return grouper


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
                   MinusPlugin(),
                   )


def make_parser(default_field='text', plugins=DEFAULT_PLUGINS, schema=None,
                int_fields=None, yesno_fields=None, aliases=None):
    '''Helper function to create a QueryParser.
    
    Parameters:
        default_field: the default field to search against for non-field
                        queries
        plugins: a list of plugins to use when parsing
        schema: If provided, a schema to check fieldnames against. If not
                provided, any query of the form "foo:bar" will yield searches
                against the "foo" field; if provided and "foo" is not a field,
                then the search will look for "foo bar" in the default_field.
                NOTE: If provided, search queries MUST use unicode
        int_fields: A list of fields that expect integer values from
                    CloudSearch
        yesno_fields: A list of fields to convert "yes" and "no" queries to
                      boolean 1 / 0 searches
        aliases: A dictionary of aliases to use for the AliasPlugin
    
    '''
    parser = whoosh.qparser.default.QueryParser(default_field, schema,
                                                plugins=plugins)
    parser_parse = parser.parse
    def parse(text, *args, **kwargs):
        assert isinstance(text, unicode), 'Cannot parse non-unicode objects (%r)' % text
        return parser_parse(text, *args, **kwargs)
    parser.parse = parse
    parser.parse.__doc__ = parser_parse.__doc__
    if int_fields:
        parser.add_plugin(IntNodePlugin(int_fields))
    if yesno_fields:
        parser.add_plugin(YesNoPlugin(yesno_fields))
    if aliases:
        parser.add_plugin(FieldAliasPlugin(aliases))
    return parser


def make_schema(fields, datefields=()):
    '''Create a whoosh.fields.Schema object from a list of field names.
    All fields will be set as TEXT fields. If datefields is supplied,
    additionally create DATETIME fields with those names
    
    '''
    fields = dict.fromkeys(fields, whoosh.fields.TEXT)
    if datefields:
        datefields = dict.fromkeys(datefields, whoosh.fields.DATETIME)
        fields.update(datefields)
    return whoosh.fields.Schema(**fields)


def convert(query, parser):
    parsed = parser.parse(query)
    pieces = walk_clause(parsed)
    return u''.join(pieces)


def __sample_parser(schema=None):
    return make_parser(int_fields=["count", "number"],
                       yesno_fields=["active", "ready"],
                       aliases={"alias": ["alias1", "alias2"]},
                       schema=schema)


def __sample_schema():
    return make_schema(["foo", "bar", "baz", "count", "number", "active",
                        "text", "ready", "active", "alias", "alias1",
                        "alias2"])


def main(args):
    '''For command line experimentation. Sample output:
    
    $ python l2cs.py 'foo:bar AND baz:bork'
    Lucene input: foo:bar AND baz:bork
    Parsed representation: And([Term(u'foo', u'bar'), Term(u'baz', u'bork')])
    Lucene form: (foo:bar AND baz:bork)
    Cloudsearch form: (and (field foo 'bar') (field baz 'bork'))
    
    '''
    args = [unicode(u, 'utf-8') for u in args[1:]]
    schema = __sample_schema() if "--schema" in args else None
    if schema:
        args.pop(args.index("--schema"))
    query = u' '.join(args)
    print "Lucene input:", query
    parser = __sample_parser(schema=schema)
    parsed = parser.parse(query)
    print "Parsed representation:", repr(parsed)
    print "Lucene form:", unicode(parsed)
    cloudsearch_query = ''.join(walk_clause(parsed))
    print "Cloudsearch form:", cloudsearch_query


if __name__ == '__main__':
    main(sys.argv)
