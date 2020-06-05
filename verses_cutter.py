# -*- Encoding: utf-8 -*-
from processor_basic import ProcessorBasic, fill_arg_for_processor
from lxml import sax
from lxml import etree

MAX_LINES_IN_VERSE = 420


class SaxError(etree.LxmlError):
    """General SAX error.
    """


class MyContentHandler(sax.ElementTreeContentHandler):
    def __init__(self):
        super().__init__()
        # sax.ElementTreeContentHandler.__init__(self)
        self.br_count = 0
        self.nstack = 0
        self.verse_nstack = -1

    def startElementNS(self, name, qname, attributes):
        super().startElementNS(name, qname, attributes)
        self.nstack += 1
        _, local_name = name
        if local_name == 'p' and attributes.get((None, 'class'), '') == 'verse':
            if self.verse_nstack == -1:
                self.verse_nstack = self.nstack
            if self.verse_nstack != self.nstack:
                Exception()
            self.br_count = 0

    def endElementNS(self, name, qname):
        super().endElementNS(name, qname)
        self.nstack -= 1
        _, local_name = name
        if local_name == 'br':
            self.br_count += 1
            if self.br_count > MAX_LINES_IN_VERSE:
                super().endElementNS((None, 'p'), 'p')
                super().startElementNS((None, 'p'), 'p', {(None, 'class'): 'verse'})
                self.br_count = 0


class VersesCutter(ProcessorBasic):

    def process_lxml_tree(self, tree):
        handler = MyContentHandler()
        sax.saxify(tree, handler)
        return handler.etree


if __name__ == '__main__':
    parser = fill_arg_for_processor('verses cutter')
    parser_args = parser.parse_args()
    cutter = VersesCutter(parser_args)
    cutter.process()
