# -*- Encoding: utf-8 -*-
""" Генерация общей схемы для документов выбранного корпуса. Схема генерируется в пользовательском формате"""

import os
from lxml import etree

from processor_basic import ProcessorBasic, fill_arg_for_processor

TAG_POS = 0
ELEM_POS = 1
ATTR_POS = 2
TEXT_POS = 3
TAIL_POS = 4
FIRST_DOC_POS = 5

HAS = 0
HASNT = 1
MIXED = 2

to_str = {HAS: 'has', HASNT: "hasn't",  MIXED: 'mixed'}


class Schema(ProcessorBasic):
    def __init__(self, args):
        super(Schema, self).__init__(args)
        self.glob_info = dict()
        self.schema = args.schema
        self.outfile = None
        self.common_part = None

    @staticmethod
    def check_text(text_info, text):
        val = HASNT if text is None or text == '' or text.isspace() else HAS
        if text_info is None:
            return val
        return val if text_info == val else MIXED

    def get_info(self, tree, info):
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
            info[ELEM_POS][elem.tag] = self.get_info(elem, elem_info)
        return info

    def process_lxml_tree(self, tree):
        path_list = os.path.normpath(self.inpname).split(os.path.sep)[:-1]
        if self.common_part is None:
            self.common_part = path_list
        else:
            for i in range(len(self.common_part)):
                if self.common_part[i] != path_list[i]:
                    self.common_part = self.common_part[:i]
                    break
        root = tree.getroot()
        root_info = self.glob_info.get(root.tag, None)
        self.glob_info[root.tag] = self.get_info(root, root_info)
        return tree

    def outfile_write(self, text):
        # if isinstance(text,unicode):
        #   text = text.encode(encoding='utf-8')
        self.outfile.write(text)

    def put_info(self, info, shift):
        self.outfile_write(shift)
        self.outfile_write(info[TAG_POS])
        if len(info[ATTR_POS]) > 0:
            start = True
            for attr in info[ATTR_POS]:
                self.outfile_write('{' if start else ',')
                self.outfile_write(attr)
                start = False
            self.outfile_write('}')
        # self.outfile_write('['+to_str[info[TEXT_POS]]+', '+to_str[info[TAIL_POS]]+']')
        self.outfile_write('\t' + os.path.relpath(info[FIRST_DOC_POS], self.common_part)+'\t\n')
        for value in info[ELEM_POS].values():
            self.put_info(value, shift+info[TAG_POS]+'/')

    def process(self):
        inp_paths = self.inppath.split('|')
        for self.inppath in inp_paths:
            if not super(Schema, self).process():
                return
        self.common_part = os.sep.join(self.common_part)
        with open(self.schema, 'w') as self.outfile:
            self.outfile_write('tags sequence\texample\tcomment\n')
            for value in self.glob_info.values():
                self.put_info(value, '')
            self.outfile_write('\n(common path of examples - '+self.common_part+')')


if __name__ == '__main__':
    parser = fill_arg_for_processor('schema processing')
    parser.add_argument('--schema', required=True)
    parser_args = parser.parse_args()
    processor = Schema(parser_args)
    processor.process()
