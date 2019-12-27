# -*- Encoding: utf-8 -*-

from processor_basic import ProcessorBasic, fill_arg_for_processor
import operator
from lxml import etree
import unicodedata

class SymbolCounter(ProcessorBasic):

    def __init__(self, argv):
        # self.counter = Counter()
        self.counter = dict()
        self.sym_stat = argv.sym_stat
        super(SymbolCounter, self).__init__(argv)

    def count_text(self, text):
        if text is None or text == '' or text.isspace():
            return
        for sym in text:
            self.counter[sym] = self.counter.setdefault(sym,0)+1

    def process_lxml_tree(self, tree):
        root = tree.getroot()
        body = root.find('body')
        for elem in body.iter():
            if elem.tag is etree.PI or elem.tag is etree.Comment:
                continue
            self.count_text(elem.tail)
            if elem.tag != 'span' and  elem.tag != 'noindex':
                self.count_text(elem.text)

    def get_stat(self):
        return sorted(self.counter.items(), key=operator.itemgetter(1), reverse=True)

    def report(self):
        try:
            with open(self.sym_stat, 'w') as f_count:
                for stat in self.get_stat():
                    sym = stat[0]
                    if isinstance(sym, str):
                        sym = sym.decode(encoding='utf-8')

                    if len(sym) > 1:
                        raise Exception('logic error')
                    cat = unicodedata.category(sym)
                    try:
                        sym_name = unicodedata.name(sym)
                    except ValueError as e:
                        sym ='#{0}'.format(ord(sym))
                        sym_name = 'UNKNOWN NAME'
                    catGr = cat[0]
                    count = stat[1]
                    if catGr == 'L' or cat == 'Cc' or cat == 'Nd':
                        continue
                    if isinstance(sym, unicode):
                        sym = sym.encode(encoding='utf-8')
                    f_count.write('"{0}" {1}, {2}: {3} time(s)\n'.format(sym, cat, sym_name, count))
        except (OSError, IOError) as e:
            self.fatal_error("can't write statistics into {0}: {1}".format(self.sym_stat, e.message))


if __name__ == '__main__':
    parser = fill_arg_for_processor('symbol counter')
    parser.add_argument('--sym_stat', required=True)
    parser_args = parser.parse_args()
    counter = SymbolCounter(parser_args)
    counter.process()
    counter.report()


