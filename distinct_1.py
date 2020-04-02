# -*- Encoding: utf-8 -*-
from converter_basic import ConverterBasic, fill_arg_for_converter
from lxml import etree
from lxml_ext import LxmlExt


class Distinct1(ConverterBasic):


    @staticmethod
    def fill_speech(tree):
        attrs = None
        for speech in tree.getroot().iter('speech'):
            if speech.attrib:
                attrs = speech.attrib
            elif attrs is not None:
                speech.attrib.update(attrs)

    def join_noindex(self, tree):
        for noindex in tree.getroot().iter('noindex', 'span'):
            if noindex.tag == 'span' and noindex.attrib.get("class", "") in ("note", "head"):
                noindex.tag = 'noindex'
                noindex.attrib.clear()
                if not self.is_empty(noindex.text):
                    noindex.text = '[' + noindex.text + ']'
            prev = noindex.getprevious()
            if prev is None or prev.tag is etree.PI or prev.tag is etree.Comment or prev.tag != 'noindex':
                continue
            if self.is_empty(prev.tail):
                txt = LxmlExt.concat_text(prev.text, prev.tail)
                noindex.text = LxmlExt.concat_text(txt, noindex.text)
                prev.getparent().remove(prev)

    @staticmethod
    def check_distinct_separ(text, before_distinct):
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
        self.join_noindex(tree)
        self.fill_speech(tree)


if __name__ == '__main__':
    parser = fill_arg_for_converter('distinct1')
    parser_args = parser.parse_args()
    distinct1 = Distinct1(parser_args)
    distinct1.process()
