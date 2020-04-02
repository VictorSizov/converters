# -*- Encoding: utf-8 -*-

import sys
import re
from converter_basic import ConverterBasic, fill_arg_for_converter

COMBINING_GRAVE_ACCENT = u'\u0300'  # ◌̀
COMBINING_ACUTE_ACCENT = u'\u0301'  # ◌́


class ConverterStihi(ConverterBasic):

    """def check_contain_http(self, elem, check_text):
        if self.nostructured(elem):
            return
        (text, label) = (elem.text, 'text') if check_text else (elem.tail, 'tail')
        if text is None or "http://" not in text:
            return
        self.line = elem.sourceline
        self.err_proc("http address in {0} of {1}".format(label, elem.tag))
        self.line = -1
    """

    def change_accent(self, text):
        if text is None:
            return text
        n = text.count(COMBINING_GRAVE_ACCENT)
        if n == 0:
            return text
        self.count_mess("COMBINING_GRAVE_ACCENT changed to COMBINING_ACUTE_ACCENT", n)
        return text.replace(COMBINING_GRAVE_ACCENT, COMBINING_ACUTE_ACCENT)

    def process_lxml_tree(self, tree):
        root = tree.getroot()
        body = root.find('body')
        if body is None:
            return
        for elem in body.iter():
            if self.nostructured(elem):
                continue

            elem.text = self.change_accent(elem.text)
            elem.tail = self.change_accent(elem.tail)


if __name__ == '__main__':
    parser = fill_arg_for_converter('speech converter')
    parser_args = parser.parse_args()
    converter = ConverterStihi(parser_args)
    converter.process()
