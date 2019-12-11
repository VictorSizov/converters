# -*- Encoding: utf-8 -*-


from validator_basic import ValidatorBasic
from processor_basic import fill_arg_for_processor


class Validator(ValidatorBasic):

    def process_lxml_tree(self, tree):
        if not super(Validator, self).process_lxml_tree(tree):
            return False
        root = tree.getroot()
        is_manual = 'manual' in self.inpname
        self.validate_outbound_text(root, 'body')
        if is_manual:
            self.validate_outbound_text(root, 'speech')


if __name__ == '__main__':
    parser = fill_arg_for_processor('speech validator')
    parser.add_argument('--schema', required=True)
    parser_args = parser.parse_args()
    validator = Validator(parser_args)
    validator.process()
