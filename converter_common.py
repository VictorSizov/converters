# -*- Encoding: utf-8 -*-

from converter_base import ConverterBase


class ConverterCommon(ConverterBase):

    @staticmethod
    def format(tree):
        root = tree.getroot()
        for el in root.iter():
            if el.tag == 'speach':
                el.tag = 'speech'

            if el.tail is None or el.tail == '':
                el.tail = '\n'
            elif '\n' not in el.tail:
                el.tail += '\n'
            else:
                while len(el.tail) >= 2 and el.tail[-2] == '\n':
                    el.tail = el.tail[:-1]

    @staticmethod
    def sort_attr(tree):
        root = tree.getroot()
        for el in root.iter():
            attrib = el.attrib
            cmpattr = ''
            for attr in attrib:

                if attr < cmpattr:
                    attributes = sorted(attrib.items())
                    attrib.clear()
                    attrib.update(attributes)
                    break
                else:
                    cmpattr = attr

    @staticmethod
    def old_norm(tree):
        root = tree.getroot()
        for el in root.iter():
            attributes = dict()
            if el.tag == 'speach':
                el.tag = 'speech'
            if el.tag == 'speech':
                for key, val in el.items():
                    if key == 'role':
                        attributes['actor'] = val
                    else:
                        attributes[key] = val
            else:
                attributes = el.attrib
            attributes2 = sorted(attributes.items())
            el.attrib.clear()
            el.attrib.update(attributes2)

    @staticmethod
    def clear_ln(tree):
        root = tree.getroot()
        for sp in root.iter('speech'):
            for el in sp.iter():
                if el.tag == 'speech':
                    continue
                if el.text is not None:
                    el.text = el.text.replace('\n', ' ')
                    el.text = el.text.replace('  ', ' ')
                if el.tail is not None:
                    el.tail = el.tail.replace('\n', ' ')
                    el.tail = el.tail.replace('  ', ' ')

    def convert_file_lxml(self, tree):
        if self.action == 'format':
            self.format(tree)
        elif self.action == 'sortattr':
            self.sort_attr(tree)
        elif self.action == 'clearln':
            self.clear_ln(tree)
        elif self.action == 'old_norm':
            self.old_norm(tree)
        else:
            raise Exception('logic error')
