# -*- Encoding: utf-8 -*-

import re
import os
import sys
from lxml import etree

from converter_base import ConverterBase

TAG_POS = 0
ELEM_POS = 1
ATTR_POS = 2
TEXT_POS = 3
TAIL_POS = 4
FIRST_DOC_POS = 5

HAS = 0
HASNT = 1
MIXED = 2

to_str = {HAS:'has', HASNT:"hasn't",  MIXED:'mixed'}


class Test(ConverterBase):
    def __init__(self, args):
        ConverterBase.__init__(self, args)
        self.glob_info = dict()
        self.outfile = None

    @staticmethod
    def check_text(text_info, text):
        val = HASNT if text is None or text == '' or text.isspace() else HAS
        if text_info is None:
            return val
        return val if text_info == val else MIXED

    def process(self, tree, info):
        if info is None:
            info = [tree.tag, dict(), set(), None, None, self.inpname + ';' + str(tree.sourceline)]
        info[TEXT_POS] = self.check_text(info[TEXT_POS], tree.text)
        info[TAIL_POS] = self.check_text(info[TAIL_POS], tree.tail)
        for attr in tree.attrib:
            info[ATTR_POS].add(attr)
        for elem in tree.getchildren():
            if elem.tag is etree.PI or elem.tag is etree.Comment:
                continue
            elem_info = info[ELEM_POS].get(elem.tag, None)
            info[ELEM_POS][elem.tag] = self.process(elem, elem_info)
        return info

    def convert_file(self, inpfile, outfile):
        try:
            self.inpname = inpfile
            tree = etree.parse(inpfile)
            root = tree.getroot()
            root_info = self.glob_info.get(root.tag, None)
            self.glob_info[root.tag] = self.process(root, root_info)
        except etree.LxmlError as e:
            self.wrong_docs += 1
            if self.line != -1:
                print >> sys.stderr, 'Error in', inpfile, 'line', self.line, ':', e.message
            print >> sys.stderr, 'Error in', inpfile, ':', e.message

    def pr_info(self, info, shift):
        self.outfile.write(shift)
        self.outfile.write(info[TAG_POS])
        if len(info[ATTR_POS]) > 0:
            start = True
            for attr in info[ATTR_POS]:
                self.outfile.write('{' if start else ',')
                self.outfile.write(attr)
                start = False
            self.outfile.write('}')
        self.outfile.write('['+to_str[info[TEXT_POS]]+', '+to_str[info[TAIL_POS]]+']')
        self.outfile.write(': ' + info[FIRST_DOC_POS])
        self.outfile.write('\n')
        for value in info[ELEM_POS].values():
            self.pr_info(value, shift+'\t')

    def convert(self):
        ConverterBase.convert(self)
        with open(self.outpath+'/schema.txt', 'w') as self.outfile:
            for value in self.glob_info.values():
                self.pr_info(value, '')


