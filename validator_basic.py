# -*- Encoding: utf-8 -*-
"""
ValidatorBasic - базовый класс для валидаторов,
реализована проверка соответствия xsd-схеме
и список частотности ошибок
"""


from lxml import etree
import csv
import os
from error_processor import ProgramTerminated, expanduser
import collections
import string
from lxml_ext import LxmlExt

from processor_basic import ProcessorBasic, fill_arg_for_processor
TEXT_REJECT = 0
TEXT_COMMENT = 1
TEXT_TEXT = 2


class ValidatorBasic(ProcessorBasic):

    wrong_symbols = '{}'

    def __init__(self, args):
        """инициализация имени схемы"""
        self.schema_name = expanduser(args.schema)
        self.table_name = expanduser(args.table)
        self.valid_path_symbols = set(string.ascii_letters+string.digits+u"-+=_/\\.")
        super(ValidatorBasic, self).__init__(args)

    def check_date(self, key, value, value_src, prefix):
        ret = u'{0} {1}="{2}": '.format(prefix, key, value_src)
        try:
            val = int(value)
        except ValueError:
            self.err_proc(ret + u'wrong number format')
            return
        if key == 'age':
            if not 1 < val <= 100:
                self.err_proc(ret + u'condition "1 < age < 100" has not been met')
        if key == 'birth':
            if not 1750 < val < 2019:
                self.err_proc(ret + u'condition "1750 < birth date < 2019" has not been met')

    def check_age_birth(self, key, value):
        if '-' in value:
            values = value.split('-')
            if len(values) != 2 or values[0] == '' or values[1] == '':
                self.err_proc(u'attribute {0}="{1}": wrong number format'.format(key, value))
                return
            self.check_date(key, values[0], value, u'low bound')
            self.check_date(key, values[1], value, u'upper bound ')
        else:
            self.check_date(key, value, value, u'attribute ')

    def check_distinct(self, root):
        for distinct in root.iter('distinct'):
            self.line = distinct.sourceline
            form = distinct.attrib.get("form", None)
            if form is None:
                self.err_proc('distinct tag should have attribure "form"')
            ln = len(distinct)
            if ln != 0:
                self.err_proc('distinct tag should not contain any tag')
            if not LxmlExt.is_informative(distinct.text):
                self.err_proc('distinct tag should contain alphanumeric text')

    def get_text_type(self, elem):
        raise Exception("should be rewriten in child class")

    def check_wrong_sym(self, text):
        src = set(text)
        wrong = list(src.intersection(self.wrong_symbols))
        if wrong:
            self.err_proc('text contains wrong symbols from set "{0}"'.format(wrong))

    def check_outbound_text(self, text, tag):
        """сообщение о наличии непробельного текста"""
        if self.is_empty(text):
            return
        if len(text) < 6:
            pass
        example = text.replace('\n', '\\n')
        mess = u'Text is directly into tag {0}'.format(tag)
        self.err_proc(mess, example)

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

    def process_lxml_tree(self, tree):
        """проверка соответствия xml-дерева схеме,
        вывод ошибок в случае несоответствия"""
        if self.schema.validate(tree):
            return tree

        for error in self.schema.error_log:
            self.line = error.line
            self.err_proc(error.message)
        return None

    def check_names(self, paths):
        for path in paths:
            wrong = set(path).difference(self.valid_path_symbols)
            if wrong:
                mess = u','.join("'"+s+"'" for s in sorted(list(wrong)))
                mess = mess.replace("' '", "<space>")
                self.err_proc("File name {0} in table contains wrong symbol(s) {1}. ".
                              format(path, mess))

    def process_row(self, row, nn):
        restkey = row.get('###', None)
        if restkey is not None:
            nom = len(row)
            for key in restkey:
                if key is not None and key != '':
                    self.err_proc('row {0} contains column {1}, table sould have no more than {2} columns'.format(
                        nn+1, nom, len(row) - 1))
                nom += 1
        self.line += 1
        return row['path'].lower()

    def get_paths(self, inppath):
        """ Получение списка xml-файлов для обработки
            список формирует get_paths() базового класса
            Если параметер --table был указан,
                из csv-таблицы с этим именем читается список файлов для обработки.
                и проверяется на совпадение со списком из файлов, лежащих в inppath и ее подпапках.
            Иначе вызывается get_paths() базового класса
            """
        paths = super(ValidatorBasic, self).get_paths(inppath)
        #  self.check_names(paths, False)
        if self.table_name is None:
            return paths
        try:
            with open(self.table_name, 'r', encoding="utf-8") as f:
                self.inpname, self.line = self.table_name, 1
                dict_reader = csv.DictReader(f, delimiter=';', restkey='###', strict=True,)
                cmp_paths_list = [self.process_row(row, nn) for nn, row in enumerate(dict_reader)]
                self.inpname, self.line = None, -1
        except (OSError, IOError) as e:
            self.fatal_error("can't read data from table " + self.table_name)
        #  проверка на наличие дублей
        for item, count in collections.Counter(cmp_paths_list).most_common():
            if count == 1:
                break
            self.err_proc('File name {0} repeats in table  {1} time(s)'.format(item, count))
        cmp_paths_set = set(cmp_paths_list)
        self.check_names(sorted(cmp_paths_set))
        paths_set = {os.path.splitext(path.lower().replace('\\', '/'))[0] for path in paths}
        self.line = -1
        if paths_set != cmp_paths_set:
            missed = cmp_paths_set.difference(paths_set)
            extra = paths_set.difference(cmp_paths_set)
            for path in missed:
                self.err_proc("File  {0}, mentioned in {1} not found".format(path, self.table_name))
            for path in extra:
                self.err_proc("File {0} is not mentioned in {1}".format(path, self.table_name))
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


def add_arguments(title):
    parser = fill_arg_for_processor(title)
    parser.add_argument('--schema', required=True)
    parser.add_argument('--ignore_mess', default=None)
    parser.add_argument('--show_mess', default=None)
    parser.add_argument('--show_files', default=None)
    parser.add_argument('--limit', type=int, default=-1)
    parser.add_argument('--table', default=None)
    return parser

