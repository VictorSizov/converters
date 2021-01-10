# -*- Encoding: utf-8 -*-

import sys
from validator_basic import ValidatorBasic, add_arguments


class ValidatorStihi(ValidatorBasic):

    def check_contain_http(self, elem, check_text):
        if self.nostructured(elem):
            return
        (text, label) = (elem.text, 'text') if check_text else (elem.tail, 'tail')
        if text is None or "http://" not in text:
            return
        self.line = elem.sourceline
        self.err_proc("http address in {0} of {1}".format(label, elem.tag))
        self.line = -1

    def process_lxml_tree(self, tree):
        tree = super(ValidatorStihi, self).process_lxml_tree(tree)
        if not tree:
            return None
        root = tree.getroot()
        for para in root.iter('p'):
            if para is None:
                self.err_proc('poetic text is eeeempty')
            if len(para) == 0 and self.is_empty(para.text):
                self.line = para.sourceline
                self.err_proc('poetic text is empty')
                self.line = -1
            self.check_contain_http(para, True)
            for elem in para.iter():
                self.check_contain_http(elem, True)
                self.check_contain_http(elem, False)
        return tree


if __name__ == '__main__':
    parser = add_arguments('speech validator')
    parser_args = parser.parse_args()
    validator = ValidatorStihi(parser_args)
    if not validator.process() or validator.error_processor.err_num > 0:
        sys.exit(1)
