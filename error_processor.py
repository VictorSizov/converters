# -*- Encoding: utf-8 -*-
import os
import sys
from collections import Counter


class ProgramTerminated(Exception):
    pass


def expanduser(path):  # подставляет home directory  вместо ~
    if path is None:
        return None
    return os.path.expanduser(path)


class ErrorProcessor(object):
    def __init__(self, kwargs):
        # инициализация параметров:
        self.ignore_mess_name = expanduser(kwargs.get('ignore_mess', None))
        self.ignore_mess = None
        self.show_mess_name = expanduser(kwargs.get('show_mess', None))
        self.show_mess = None
        self.show_files_name = kwargs.get('show_files', None)
        self.stat_name = expanduser(kwargs.get('stat', None))
        self.limit = kwargs.get('limit', -1)
        self.inppath = expanduser(kwargs['inppath'])
        self.show_file = None

        self.err_report_name = expanduser(kwargs.get('err_report', None)) # имя файла для ошибок
        self.mess_counter = Counter() if self.stat_name is not None else None
        self.wrong_docs = set()
        self.err_num = 0
        self.err_report = None
        self.step = ''

    def count_mess(self, mess, num=1):
        if self.mess_counter is None:
            return
        self.mess_counter[mess] = self.mess_counter[mess] + num

    def fatal_error(self, mess):
        sys.stderr.write(mess + '\nprogram terminated\n')
        raise ProgramTerminated()

    def err_report_step(self, step):
        if self.err_report_name is None:
            return
        self.step = step
        if self.err_report is not None:
            self.err_report.close()
            self.err_report = None

    @staticmethod
    def try_create_folder(file_path):
        path = os.path.split(file_path)[0]
        if path is None or path == '':
            return
        if not os.path.exists(path):
            os.makedirs(path)

    def open_log(self,):
        try:
            if self.err_report_name is None:
                sys.stdout.reconfigure(encoding='utf-8')
                self.err_report = sys.stdout
                # sys.stdout = open(os.devnull, 'w')
            else:
                err_report_name = self.err_report_name
                if self.step != '':
                    (err_report_name, ext) = os.path.splitext(err_report_name)
                    err_report_name += str(self.step) + ext
                self.try_create_folder(err_report_name)
                self.err_report = open(err_report_name, 'w', encoding="utf-8")
        except (OSError, IOError) as e:
            self.fatal_error("Can't open message file " + self.err_report_name)

    def load_mess_data(self, filename):
        try:
            if filename is not None:
                with open(filename, 'r') as f:
                    return f.read().splitlines()
        except (OSError, IOError) as e:
            self.fatal_error("Can't load list of ignored messages " + filename)

    def load_ignore_mess(self):
        if self.ignore_mess_name is not None and self.show_mess_name is not None:
            self.fatal_error("You shouldn't use '--ignore_mess' and '--show_mess' together")
        self.ignore_mess = self.load_mess_data(self.ignore_mess_name)
        self.ignore_mess_name = None
        self.show_mess = self.load_mess_data(self.show_mess_name)
        self.show_mess_name = None

    def print_message(self, mess):
        if self.err_report is None:  # если файл для вывода сообщения не проинициализирован
            self.open_log()
        # if isinstance(mess, unicode):
            # mess = mess.encode(encoding='utf-8')
        self.err_report.write(mess+'\n')
        self.err_num += 1
        if self.limit != -1 and self.limit <= self.err_num:
            self.fatal_error('Message number exceed '+str(self.limit))

    def check_ignore(self, mess):
        # if isinstance(mess, unicode):
            # mess = mess.encode('utf-8')
        if self.show_mess is not None:
            return mess not in self.show_mess
        return self.ignore_mess is not None and mess in self.ignore_mess

    def err_file_report(self, f_name):
        if self.show_files_name is None:
            return
        if f_name in self.wrong_docs:
            return
        self.wrong_docs.add(f_name)
        if self.show_file is None:
            self.show_file = open(self.show_files_name, "w")
        self.show_file.write(f_name + '\n')


    def proc_message(self, mess, f_name=None, line=-1, example=''):
        if self.check_ignore(mess):
            return
        self.count_mess(mess)
        full_mess = ''
        if f_name is not None:
            # self.wrong_docs.add(f_name)
            self.err_file_report(f_name)
            if self.inppath is not None:
                f_name = os.path.join(self.inppath, f_name)
            full_mess = 'File "' + f_name + '"'
        if line != -1:
            if full_mess:
                full_mess += ', '
            full_mess += 'line '+str(line)
        if full_mess:
            full_mess +='\n'
        full_mess += mess
        if example != '':
            full_mess += '('+example+')'
        self.print_message(full_mess)

    def report(self):
        if self.wrong_docs:
            mess = "errors found in {0} documents.\n".format(len(self.wrong_docs))
            sys.stdout.write(mess)
            if self.err_report is not sys.stdout:
                self.err_report.write(mess)
                sys.stdout.write('See ' + self.err_report_name+'\n')
        if self.mess_counter:
            self.try_create_folder(self.stat_name)
            try:
                with open(self.stat_name, 'w', encoding="utf-8") as f_count:
                    for err in self.mess_counter.most_common():
                        err_txt = err[0]
                        # if isinstance(err_txt, unicode):
                            # err_txt = err_txt.encode(encoding='utf-8')
                        f_count.write(err_txt + ': ' + str(err[1]) + ' time(s)\n')
            except Exception as e:
                self.fatal_error("can't write statistics into " + self.stat_name)
