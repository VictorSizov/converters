# -*- Encoding: utf-8 -*-
"""
ValidatorBasic - базовый класс для валидаторов,
реализована проверка соответствия xsd-схеме
и список частотности ошибок
"""


from lxml import etree
import csv
import os
import sys
from process_table import ProcessorTable, ProcessorVideoTable

from typing import List

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
    # valid_filename_symbols = set(string.ascii_letters+string.digits+"-+._/\\")

    def __init__(self, args):
        super(ValidatorBasic, self).__init__(args)

        root = expanduser(self.inppaths)
        if root.find(';') != -1:
            self.fatal_error("{0} contains ';'".format(root))
        self.inppaths = os.path.join(root, "texts")
        name = os.path.basename(root)
        self.table_name = os.path.join(root, "tables", name+".csv")
        self.corp_root = os.path.dirname(root)
        """инициализация имени схемы"""
        schema_name = args.scheme
        self.schema_name = schema_name if schema_name and os.path.exists(schema_name) else None
        self.valid_path_symbols = set(string.ascii_letters+string.digits+u"-+=_/\\.")
        self.media = args.media
        self.schema = None
        """ Костыль для удаления необработанных файлов"""
        self.del_path = None
        if os.path.basename(self.table_name)=="murco.csv":
            with open(os.path.join(os.path.dirname(self.table_name),"new.txt")) as del_f:
                self.del_path = {s.rstrip('\n') for s in del_f}

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
        super().process_lxml_tree(tree)
        if self.schema:
            if self.schema.validate(tree):
                return tree
            for error in self.schema.error_log:
                self.line = error.line
                self.err_proc(error.message)
        for sent in tree.getroot().iter("se"):
            if len(sent) == 0:
                self.set_line_info(sent)
                self.err_proc("empty sentence")
        return None

    def process_file(self, inpfile):
        self.line = -1
        url = os.path.join(self.inppath, inpfile) if inpfile != '' else self.inppath
        url = os.path.relpath(url, self.corp_root)
        url_utf8 = url.encode('utf8')
        if len(url_utf8) > 235:
            self.line = -1
            self.err_proc("s_url '{0}', generated from filename, is too long".format(url))
        return super().process_file(inpfile)

    def check_names(self, paths):
        self.inpname = None
        for path in paths:
            wrong = set(path).difference(self.valid_path_symbols)
            if wrong:
                mess = u','.join("'"+s+"'" for s in sorted(list(wrong)))
                mess = mess.replace("' '", "<space>").encode('utf-8')
                self.err_proc("File name {0} in table contains wrong symbol(s) {1}. ".
                              format(path, mess))
    '''
    def process_row(self, nn, row) -> List[str]:
        rest_key = row.get('###', None)
        if rest_key is not None:
            nom = len(row)
            for key in rest_key:
                if key is not None and key != '':
                    self.err_proc('row {0} contains column {1}, table should have no more than {2} columns'.format(
                        nn+1, nom, len(row) - 1))
                nom += 1
        self.line += 1
        return row['path'].lower()

    def process_table(self, table_name: str) -> List[str]:
        """ Loading and process table data. Default processing function (process_reader=None)
        check table data"""
        try:
            with open(table_name, 'r') as f:
                self.inpname, self.line = table_name, 1
                dict_reader = csv.DictReader(f, delimiter=';', restkey='###', strict=True, )
                cmp_paths_list = list()
                for nn, row in enumerate(dict_reader, 2):
                    cmp_paths_list.append(self.process_row(nn, row))
        except (OSError, IOError) as e:
            self.fatal_error("can't read data from table " + table_name)
        except csv.Error as ee:
            self.fatal_error("wrong string {0} in table {1}. Exception {2}".format(nn, table_name, ee))

        #  проверка на наличие дублей
        for item, count in collections.Counter(cmp_paths_list).most_common():
            if count == 1:
                continue
            self.err_proc('File name {0} repeats in table  {1} time(s)'.format(item, count))
        return cmp_paths_list
    '''
    @staticmethod
    def cut_elements(arr, split_data, cut_data=None):
        for n, ss in enumerate(arr):
            sss = ss.split(split_data)
            if not cut_data or sss[-1] in cut_data:
                arr[n] = split_data.join(sss[:-1])
        return arr

    def check_media_path(self, paths_set):
        err = set()
        paths_set_groups = set()
        for p in paths_set:
            p_split = p.split('/')
            if len(p_split) < 3:
                self.error_processor.print_message("{0}: too few folders".format(p))
            if p_split[-2] != 'texts':
                if p_split[-2] not in ("table_acts", "table_gest"):
                    self.error_processor.print_message("{0}: too few folders".format(p))
                continue
            cmp_folder = p_split[-3]
            cmp_file = p_split[-1]
            cmp_len = len(cmp_folder)
            if len(cmp_file) - 2 < len(cmp_folder) or cmp_file[:cmp_len] != cmp_folder or \
                    cmp_file[cmp_len] not in '_':
                if len(cmp_file.split('_')) > 1:
                    cmp_file = '_'.join(cmp_file.split('_')[:-1])
                err.add("{0} || {1}".format(cmp_folder, cmp_file[:cmp_len+1]))
                # self.error_processor.print_message("{0}: wrong file name format: {1} vs {2}".format(p, cmp_folder, cmp_file))
            paths_set_groups.add('/'.join(p_split[:-1]))
        return paths_set_groups


    def check_media(self, paths_set) -> List[str]:
        video_table_name = os.path.join(os.path.dirname(self.table_name), "video_ids.csv")
        video_root_name = os.path.join(self.corp_root,"tables", "video")
        video_table = ProcessorVideoTable(video_table_name, video_root_name, self.error_processor)
        video_names = self.cut_elements(video_table.process(), '.',
                                        ('avi',  'AVI', 'db', 'mp3', 'mp4', 'wav', 'wma', 'wmv', 'WMV'))
        group_paths_set = self.check_media_path(paths_set)
        # group_video_names = set(self.cut_elements(video_names, '_'))
        # mess_missed = "Clip group {{0}}_*, mentioned in {0} not found in {1}".format("murco.csv", "video_ids.csv")
        # mess_extra = "Clip group {{0}}_* from {0} is not mentioned in {1}".format("murco.csv", "video_ids.csv")
        # self.check_arrays(group_video_names, group_paths_set, mess_missed, mess_extra)
        # common_group = group_paths_set.intersection(group_video_names)
        # paths_set_cpy = {ss for ss in paths_set if ss.split('_')[:-1] in common_group}
        # video_names = {ss for ss in video_names if ss.split('_')[:-1] in common_group}
        paths_set_cpy = {ss.split('/')[-1]: ss for ss in paths_set if ss.split('/')[-3] not in self.del_path}
        # paths_set_cpy = {ss for ss in paths_set if ss.split('/')[-3] not in self.del_path}
        mess_missed = "Tagged file for clip {0} from video_ids.csv is not found"
        mess_extra = "Clip for file {0} is not found in video_ids.csv"
        self.check_arrays(set(paths_set_cpy.keys()), set(video_names), mess_missed, mess_extra,paths_set_cpy)
        return group_paths_set

    def check_arrays(self, paths_set, cmp_paths_set, mess_missed, mess_extra, full_paths=None):
        if paths_set != cmp_paths_set:
            missed = sorted(cmp_paths_set.difference(paths_set))
            extra = sorted(paths_set.difference(cmp_paths_set))
            for path in missed:
                self.error_processor.print_message(mess_missed.format(path))
            for path in extra:
                self.error_processor.print_message(mess_extra.format(full_paths[path] if full_paths else path))

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
        meta_table = ProcessorTable(self.table_name, self.error_processor)
        cmp_paths_set = set(meta_table.process())
        paths_set = {os.path.splitext(path.lower().replace('\\', '/'))[0] for path in paths}
        self.check_names(sorted(paths_set))

        if self.media:
            paths_set = self.check_media(paths_set)

        mess_missed = "File {{0}}, mentioned in {0} not found".format(self.table_name)
        mess_extra = "File {{0}} is not mentioned in {0}".format(self.table_name)
        self.check_arrays(cmp_paths_set, paths_set, mess_missed, mess_extra)
        '''
        self.inpname = None
        self.line = -1
        if paths_set != cmp_paths_set:
            missed = cmp_paths_set.difference(paths_set)
            extra = paths_set.difference(cmp_paths_set)
            for path in missed:
                self.err_proc("File  {0}, mentioned in {1} not found".format(path, self.table_name))
            for path in extra:
                self.err_proc("File {0} is not mentioned in {1}".format(path, self.table_name))
        '''
        return paths

    def process(self):
        """загрузка схемы, обработка файлов, вывод статистики ошибок"""
        try:
            if self.schema_name:
                try:
                    tree = etree.parse(self.schema_name)
                    self.schema = etree.XMLSchema(tree)
                except (OSError, IOError):
                    self.fatal_error("Can't load xsd scheme " + self.schema_name)
                except etree.LxmlError as e:
                    err_log = list(e.error_log)
                    self.fatal_error('file {0}: {1}'.format(self.schema_name, e.message))
            else:
                self.schema = None
            return super(ValidatorBasic, self).process()
        except ProgramTerminated:
            return False


def add_arguments(title):
    parser = fill_arg_for_processor(title)
    parser.add_argument('--ignore_mess', default=None)
    parser.add_argument('--show_mess', default=None)
    parser.add_argument('--show_files', default=None)
    parser.add_argument('--scheme', default=None)
    parser.add_argument('--media', default=False, action='store_true')
    return parser


if __name__ == '__main__':
    parser = add_arguments('validator')
    parser_args = parser.parse_args()
    validator = ValidatorBasic(parser_args)
    if not validator.process() or validator.error_processor.err_num > 0:
        sys.exit(1)
