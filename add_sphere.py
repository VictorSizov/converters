# -*- Encoding: utf-8 -*-
from lxml import etree

from processor_basic import ProcessorBasic, fill_arg_for_processor

class MyClass(ProcessorBasic):
    def __init__(self, args):
        super().__init__(args)
        self.rewrite = True
        self.res = open(args.found, "w")


    def process_lxml_tree(self, tree):
        head = tree.getroot().find('head')
        add_info = False
        for name in ("sphere","grsphere"):
            srch = 'meta[@name="{0}"]'.format(name)
            if not head.xpath(srch):
                head.append(etree.Element('meta', {'name': name, 'content': 'художественная'}))
                add_info = True
        if add_info:
            self.res.write(self.inpname+'\n')
        return tree

if __name__ == '__main__':
    parser = fill_arg_for_processor('verses cutter')
    parser.add_argument("--found",required=True)
    parser_args = parser.parse_args()
    cutter = MyClass(parser_args)
    cutter.process()
