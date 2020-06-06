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
        self.br_count_src = 0
        self.nstack = 0
        self.verse_nstack = -1
        self.max_br = -1

    def startElementNS(self, name, qname, attributes):
        super().startElementNS(name, qname, attributes)
        self.nstack += 1
        _, local_name = name
        if local_name == 'p' and attributes.get((None, 'class'), '') == 'verse':
            if self.verse_nstack == -1:
                self.verse_nstack = self.nstack
            if self.verse_nstack != self.nstack:
                Exception()
            if self.br_count_src > MAX_LINES_IN_VERSE:
                if self.max_br < self.br_count_src:
                    self.max_br = self.br_count_src
            self.br_count = 0
            self.br_count_src = 0

    def endElementNS(self, name, qname):
        super().endElementNS(name, qname)
        self.nstack -= 1
        _, local_name = name
        if local_name == 'br':
            self.br_count += 1
            self.br_count_src += 1
            if self.br_count > MAX_LINES_IN_VERSE:
                super().endElementNS((None, 'p'), 'p')
                super().startElementNS((None, 'p'), 'p', {(None, 'class'): 'verse'})
                self.br_count = 0


class VersesCutter(ProcessorBasic):

    def process_lxml_tree(self, tree):
        handler = MyContentHandler()
        sax.saxify(tree, handler)
        if handler.max_br > 0:
            print(self.inpname, handler.max_br, "строф")
        return handler.etree

class VersesCutter2(ProcessorBasic):
    def __init__(self, args):
        super().__init__(args)
        self.res = open(args.found, "w")


    def process_lxml_tree(self, tree):
        verses = tree.xpath('//p[@class="verse"]')
        for verse in verses:
            lines = verse.xpath("count(//br)")
            if lines > 1000:
                print(self.inpname, lines, "строк в строфе")
                self.res.write(self.inpname)
        return None




if __name__ == '__main__':
    parser = fill_arg_for_processor('verses cutter')
    parser.add_argument("--found",required=True)
    parser_args = parser.parse_args()
    cutter = VersesCutter2(parser_args)
    cutter.process()
