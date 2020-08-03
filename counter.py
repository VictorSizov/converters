# -*- Encoding: utf-8 -*-
""" Анализ знаков препинания в языках корпуса """

from processor_basic import ProcessorBasic, fill_arg_for_processor
import operator
from lxml import etree
import unicodedata
from pathlib import Path
from collections import Counter


class SymbolCounter(ProcessorBasic):

    def __init__(self, argv):
        # self.counter = Counter()
        self.counters = dict()
        self.counter = None
        self.sym_stat = argv.sym_stat
        super(SymbolCounter, self).__init__(argv)

    def count_text(self, text):
        if text is None or text == '' or text.isspace():
            return
        for sym in text:
            self.counter[sym] += 1

    def process_lxml_tree(self, tree):
        root = tree.getroot()
        for se in root.iter('se'):
            self.counter = self.counters.setdefault(se.get('lang', 'default'), Counter())
            for elem in se.iter():
                if elem.tag is etree.PI or elem.tag is etree.Comment:
                    continue
                self.count_text(elem.tail)
                if elem.tag != 'span' and elem.tag != 'noindex':
                    self.count_text(elem.text)
        return tree

    def get_stat(self):
        return sorted(self.counter.items(), key=operator.itemgetter(1), reverse=True)

    def report(self):
        try:
            root_dir = Path(self.sym_stat).expanduser()
            root_dir.mkdir(parents=True, exist_ok=True);
            for lang, l_counter in self.counters.items():
                with open(root_dir/Path(lang+".txt"), 'w') as f_count:
                    for stat in l_counter.most_common():
                        sym = stat[0]
                        if len(sym) > 1:
                            raise Exception('logic error')
                        cat = unicodedata.category(sym)
                        try:
                            sym_name = unicodedata.name(sym)
                        except ValueError:
                            sym = '#{0}'.format(ord(sym))
                            sym_name = 'UNKNOWN NAME'
                        cat_gr = cat[0]
                        count = stat[1]
                        if cat_gr == 'L' or cat == 'Cc' or cat == 'Nd':
                            continue
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
