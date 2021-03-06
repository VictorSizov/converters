# -*- Encoding: utf-8 -*-

import sys
from lxml import etree
from validator_basic import ValidatorBasic, TEXT_REJECT, TEXT_COMMENT, TEXT_TEXT, add_arguments


class ValidatorSpoken(ValidatorBasic):

    def get_attr(self, attrib, key):
        # type: (dict, unicode) -> unicode
        value = attrib.get(key, None)
        if value is not None and (value == '' or value.isspace()):
            self.err_proc(key + " attribute is empty string")
            return value if key == 'actor' else None
        return value

    def check_attr_speech(self, root):
        is_kino = '/kino/' in self.inpname or '/theater/' in self.inpname \
              or '/reading/' in self.inpname
        for speech in root.iter('speech'):
            self.line = speech.sourceline
            actor = self.get_attr(speech.attrib, 'actor')
            role = self.get_attr(speech.attrib, 'role')
            if is_kino:
                if actor is None and role is None:
                    self.err_proc('tag "speech" in cinema/theater/reading document hasn\'t actor and role attributes')
            else:
                if actor is None:
                    self.err_proc('tag "speech" in non-cinema/theater/reading document hasn\'t actor attribute')
                elif role is not None:
                    self.err_proc("tag speach in non-cinema/theater/reading document has 'role' and 'actor' attributes")
            age = self.get_attr(speech.attrib, 'age')
            if age is not None:
                self.check_age_birth('age', age)
            birth = self.get_attr(speech.attrib, 'birth')
            if birth is not None:
                self.check_age_birth('birth', birth)

    def get_text_type(self, elem):
        if elem.tag == 'span' or elem.tag == 'noindex':
            return TEXT_COMMENT
        is_manual = 'manual' in self.inpname
        if is_manual:
            if elem.tag == "se" or elem.tag == "w":
                return TEXT_TEXT
        elif elem.tag == "speech" or elem.tag == 'p' and 'verse' in elem.attrib or elem.tag == 'distinct':
            return TEXT_TEXT
        return TEXT_REJECT

    def check_empty_tags(self, root):
        body = root.find('body')
        for elem in body.iter():
            if elem.tag is etree.PI or elem.tag is etree.Comment:
                continue
            self.line = elem.sourceline
            if self.is_empty(elem.text) and len(elem) == 0 and not elem.attrib:
                self.err_proc('tag "{0}" is empty'.format(elem.tag))

    def process_lxml_tree(self, tree):
        tree = super(ValidatorSpoken, self).process_lxml_tree(tree)
        if not tree:
            return None
        root = tree.getroot()
        self.check_attr_speech(root)
        self.check_empty_tags(root)
        self.validate_text_in_tree(root)
        self.check_distinct(root)
        return tree


if __name__ == '__main__':
    parser = add_arguments('speech validator')
    parser_args = parser.parse_args()
    validator = ValidatorSpoken(parser_args)
    if not validator.process() or validator.error_processor.err_num > 0:
        sys.exit(1)
