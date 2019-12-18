# -*- Encoding: utf-8 -*-
"""
ValidatorBasic - базовый класс для валидаторов,
реализована проверка соответствия xsd-схеме
и список частотности ошибок
"""


from lxml import etree
import sys
import csv
import os
from error_processor import ProgramTerminated,expanduser

from processor_basic import ProcessorBasic
TEXT_REJECT = 0
TEXT_COMMENT = 1
TEXT_TEXT = 2


class ValidatorBasic(ProcessorBasic):

    wrong_symbols = '{}'

    def __init__(self, args):
        """инициализация имени схемы"""
        self.schema_name = expanduser(args.schema)
        self.table_name = expanduser(args.table)
        super(ValidatorBasic, self).__init__(args)

    @staticmethod
    def is_space(text):
        return text is None or text == '' or text.isspace()

    def check_date(self, key, value, value_src, prefix):
        ret = u'{0} {1}="{2}": '.format(prefix, key, value_src)
        try:
            val = int(value)
        except ValueError:
            self.err_proc(ret + u'неверный формат числа')
            return
        if key == 'age':
            if not 1 < val <= 100:
                self.err_proc(ret + u'условие 1 < возраст < 100 не выполнено')
        if key == 'birth':
            if not 1750 < val < 2019:
                self.err_proc(ret + u'условие 1750 < дата рождения < 2019 не выполнено')

    def check_age_birth(self, key, value):
        if '-' in value:
            values = value.split('-')
            if len(values) != 2 or values[0] == '' or values[1] == '':
                self.err_proc(u'атрибут {0}="{1}": неверный формат числа'.format(key, value))
                return
            self.check_date(key, values[0], value, u'нижняя граница атрибута')
            self.check_date(key, values[1], value, u'верхняя граница ')
        else:
            self.check_date(key, value, value, u'атрибут ')

    def get_text_type(self, elem):
        raise Exception("should be rewriten in child class")

    def check_wrong_sym(self, text):
        src = set(text)
        wrong = list(src.intersection(self.wrong_symbols))
        if wrong:
            self.err_proc('text contains wrong symbols from set "{0}"'.format(wrong))

    def check_outbound_text(self, text, tag):
        """сообщение о наличии непробельного текста"""
        if self.is_space(text):
            return
        if len(text) < 6:
            pass
        example = text.replace('\n', '\\n')
        mess = u'Текст непосредственно внутри тэга {0}'.format(tag)
        self.err_proc(mess.encode('utf-8'), example.encode('utf-8'))

    def validate_text(self, text, elem):
        if text is None:
            return
        ret = self.get_text_type(elem)
        if ret == TEXT_REJECT:
            self.check_outbound_text(text, elem.tag)
        elif ret == TEXT_COMMENT:
            return
        else:
            self.check_wrong_sym(text)

    def validate_text_in_tree(self, root):
        for elem in root.iter():
            if elem.tag is etree.PI or elem.tag is etree.Comment:
                continue
            self.line = elem.sourceline
            self.validate_text(elem.text, elem)
            if elem.getparent() is not None:
                self.validate_text(elem.tail, elem.getparent())

    '''
    def validate_outbound_text(self, body, tag):
        """проверка наличия непробельного текста
        внутри элемента, где его не должно быть"""
        cmpstr = u"'{0}': outbound text".format(tag)
        ignore_mess = self.error_processor.ignore_mess
        if ignore_mess is not None and cmpstr in ignore_mess:
           return
        for elem in body.iter(tag):
            self.check_outbound_text(elem, False, tag)
            for child in elem:
                self.check_outbound_text(child, True, tag)
    '''

    def process_lxml_tree(self, tree):
        """проверка соответствия xml-дерева схеме,
        вывод ошибок в случае несоответствия"""
        if self.schema.validate(tree):
            return True
        for error in self.schema.error_log:
            self.line = error.line
            self.err_proc(error.message.encode("utf-8"))
        return False


    def get_paths(self, inppath):
        """ Получение списка xml-файлов для обработки
            список формирует get_paths() базового класса
            Если параметер --table был указан,
                из csv-таблицы с этим именем читается список файлов для обработки.
                и проверяется на совпадение со списком из файлов, лежащих в inppath и ее подпапках.
            Иначе вызывается get_paths() базового класса
            """
        paths = super(ValidatorBasic, self).get_paths(inppath)
        if self.table_name is None:
            return paths
        try:
            with open(self.table_name, 'rb') as f:
                cmp_paths_set = {row['path'] for row in csv.DictReader(f, delimiter=';', strict=True)}
        except (OSError, IOError) as e:
            self.fatal_error("can't read data from table " + self.table_name)
        paths_set = {os.path.splitext(path.lower())[0] for path in paths}
        self.line = -1
        if paths_set != cmp_paths_set:
            missed = cmp_paths_set.difference(paths_set)
            extra = paths_set.difference(cmp_paths_set)
            for path in missed:
                self.err_proc("Файл {0}, указанный в {1} не найден".format(path, self.table_name))
            for path in extra:
                self.err_proc("Файл {0} не описан в {1}".format(path, self.table_name))
        return paths

    def process(self):
        """загрузка схемы, обработка файлов, вывод статистики ошибок"""
        try:
            try:
                tree = etree.parse(self.schema_name)
                self.schema = etree.XMLSchema(tree)
            except (OSError, IOError):
                self.fatal_error("Can't load xsd scheme " + self.schema_name)
            except etree.LxmlError as e:
                err_log = list(e.error_log)
                self.fatal_error('file {0}: {1}'.format(self.schema_name, e.message))
            return super(ValidatorBasic, self).process()
        except ProgramTerminated:
            return False

