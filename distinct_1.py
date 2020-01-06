# -*- Encoding: utf-8 -*-
from converter_basic import ConverterBasic,fill_arg_for_converter
from lxml_ext import LxmlExt


class Distinct1(ConverterBasic):

    def check_distinct_separ(self, text, before_distinct):
        if text is None or text == '':
            return " "
        if isinstance(text, str):
            text = text.decode('utf-8')
        sym = text[-1] if before_distinct else text[0]
        if not unicode.isspace(sym) or sym == u'\n':
            if before_distinct:
                text += u' '
            else:
                text = u' ' + text
        return text

    def process_lxml_tree(self, tree):
        for distinct in tree.getroot().iter('distinct'):
            prev = distinct.getprevious()
            if prev is None:
                prev = distinct.getparent()
                prev.text = self.check_distinct_separ(prev.text, True)
            else:
                prev.tail = self.check_distinct_separ(prev.tail, True)
            distinct.tail = self.check_distinct_separ(distinct.tail, False)


if __name__ == '__main__':
    parser = fill_arg_for_converter('distinct1')
    parser_args = parser.parse_args()
    distinct1 = Distinct1(parser_args)
    distinct1.process()
