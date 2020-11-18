# -*- Encoding: utf-8 -*-
import csv
import os
from error_processor import ErrorProcessor
from typing import List


class TableError(Exception):
    pass


class ProcessorTable:
    """
    ProcessorTable - базовый класс для обработчика nf,kbw.
    """

    def __init__(self, name: str, error_processor: ErrorProcessor=None):
        self.reader = None
        self.line = -1
        self.table_name = name
        self.error_processor = error_processor
        self.path_set = set()

    def proc_message(self, mess):
        if self.error_processor is None:
            return None
        return self.error_processor.proc_message(mess, self.table_name, self.line)

    def process_row(self, row) -> None:
        rest_key = row.get('###', None)
        if rest_key is not None:
            nom = len(row)
            for key in rest_key:
                if key is not None and key != '':
                    self.proc_message('row contains {1} columns , table should have no more than {2} columns'.format(
                        nom, len(row) - 1))
                nom += 1
        if row['path'] in self.path_set:
            self.proc_message('path: {0} встретилось более 1 раза'.format(row['path']))
        else:
            self.path_set.add(row['path'])

    def process_data(self):
        ret = []
        for self.line, row in enumerate(self.reader, 2):
            self.process_row(row)
            ret.append(row['path'].lower())
        return ret

    def process(self):
        self.line = 1
        with open(self.table_name, 'r') as f:
            self.reader = csv.DictReader(f, delimiter=';', restkey='###', strict=True, )
            try:
                return self.process_data()
            except csv.Error as ee:
                raise TableError("wrong string {0} in table {1}. Exception {2}".format(self.line, self.table_name, ee))


class ProcessorVideoTable(ProcessorTable):
    def __init__(self, table_name: str, video_root_name: str, error_processor: ErrorProcessor=None):
        super().__init__(table_name, error_processor)
        video_list_name = os.path.join(video_root_name, "video.dat")
        with open(video_list_name) as f_list:
            self.v_list = {v.rstrip('\n') for v in f_list}
        video_zero_len_name = os.path.join(video_root_name, "zero_len.dat")
        with open(video_zero_len_name) as f_list:
            self.zero_len = {v.rstrip('\n') for v in f_list}
        self.clip_set = set()


    def process_row(self, row):
        super().process_row(row)
        if row['video_id'] not in self.v_list:
            video_info = 'video "{0}" (id: {1})'.format(row['path'], row['video_id'])
            if row['video_id'] not in self.zero_len:
                self.proc_message('{0} not found'.format(video_info))
            else:
                self.proc_message('{0} has zero length'.format(video_info))
        if row['video_id'] in self.clip_set:
            self.proc_message('video_id: {0} встретилось более 1 раза'.format(row['video_id']))
        else:
            self.clip_set.add(row['video_id'])


