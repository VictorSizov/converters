# -*- Encoding: utf-8 -*-
"""
ValidatorBasic - базовый класс для валидаторов,
реализована проверка соответствия xsd-схеме
и список частотности ошибок
"""


from lxml import etree
from collections import Counter

import os
import sys

from processor_basic import ProcessorBasic


class ValidatorBasic(ProcessorBasic):

    def __init__(self, args):
        """инициализация имени схемы"""
        self.schema_name = args.schema
        self.schema = None
        self.err_dict = Counter()
        super(ValidatorBasic, self).__init__(args)

    @staticmethod
    def is_space(text):
        return text is None or text == '' or text.isspace()

    def check_outbound_text(self, elem, is_child, tag):
        """сообщение о наличии непробельного текста"""
        self.line = elem.sourceline
        checked = elem.tail if is_child else elem.text
        if self.is_space(checked):
            return
        if len(checked) < 6:
            pass
        example = checked.replace('\n', '\\n')
        mess = "'" + tag + "': outbound text (" + example + ")"
        self.err_proc(mess.encode('utf-8'))

    def validate_outbound_text(self, body, tag):
        """проверка наличия непробельного текста
        внутри элемента, где его не должно быть"""
        for elem in body.iter(tag):
            self.check_outbound_text(elem, False, tag)
            for child in elem:
                self.check_outbound_text(child, True, tag)

    def err_proc(self, mess):
        self.err_dict[mess] = self.err_dict[mess] + 1
        super(ValidatorBasic, self).err_proc(mess)

    def process_lxml_tree(self, tree):
        """проверка соответствия xml-дерева схеме,
        вывод ошибок в случае несоответствия"""
        if self.schema.validate(tree):
            return True
        for error in self.schema.error_log:
            self.line = error.line
            self.err_proc(error.message.encode("utf-8"))
        return False

    def process(self):
        """загрузка схемы, обработка файлов, вывод статистики ошибок"""
        try:
            tree = etree.parse(self.schema_name)
            self.schema = etree.XMLSchema(tree)
        except Exception as e:
            print>>sys.stderr, e.message
            return
        super(ValidatorBasic, self).process()
        err_base, ext = os.path.splitext(self.err_file_name)
        count_name = err_base + '_count' + ext
        with open(count_name, 'w') as f_count:
            for err in self.err_dict.most_common():
                f_count.write(err[0] + ': ' + str(err[1]) + 'time(s)\n')
