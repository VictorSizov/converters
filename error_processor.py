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
        self.show_files_name = expanduser(kwargs.get('show_files', None))
        self.stat_name = expanduser(kwargs.get('stat', None))
        self.limit = kwargs.get('limit', -1)
        self.inppath = expanduser(kwargs['inppath'])
        self.show_file = None
        self.limit_doc = kwargs.get('limit_doc', -1)

        self.err_report_name = expanduser(kwargs.get('err_report', None))  # имя файла для ошибок
        self.mess_counter = Counter() if self.stat_name is not None else None
        self.wrong_docs = Counter()
        self.err_num = 0
        self.err_report = None
        self.step = ''

    def count_mess(self, mess, num=1):
        if self.mess_counter is None:
            return
        self.mess_counter[mess] = self.mess_counter[mess] + num

    @staticmethod
    def fatal_error(mess):
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
                self.err_report = sys.stdout
                # sys.stdout = open(os.devnull, 'w')
            else:
                err_report_name = self.err_report_name
                if self.step != '':
                    (err_report_name, ext) = os.path.splitext(err_report_name)
                    err_report_name += str(self.step) + ext
                self.try_create_folder(err_report_name)
                self.err_report = open(err_report_name, 'w')
        except (OSError, IOError):
            self.fatal_error("Can't open message file " + self.err_report_name)

    def load_mess_data(self, filename):
        try:
            if filename is not None:
                with open(filename, 'r') as f:
                    return f.read().splitlines()
        except (OSError, IOError):
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
        self.err_report.write(mess+'\n')
        self.err_num += 1
        if self.limit != -1 and self.limit <= self.err_num:
            self.fatal_error('Message number exceed '+str(self.limit))

    def check_ignore(self, mess):
        if self.show_mess is not None:
            return mess not in self.show_mess
        return self.ignore_mess is not None and mess in self.ignore_mess

    def err_file_report(self, f_name):
        if self.show_files_name is None and self.limit_doc == -1:
            return True
        self.wrong_docs[f_name] += 1
        err_num_doc = self.wrong_docs[f_name]
        if self.limit_doc != -1 and self.limit_doc <= err_num_doc:
            if self.limit_doc == err_num_doc:
                self.err_report.write('File {0}: more then {1} errors'.format(f_name, err_num_doc))
            return False
        return True

    def proc_message(self, mess, f_name=None, line=-1, example=''):
        if self.check_ignore(mess):
            return
        self.count_mess(mess)
        full_mess = ''
        if f_name is not None:
            if self.inppath is not None:
                f_name = os.path.join(self.inppath, f_name)
            if not self.err_file_report(f_name):
                return
            full_mess = 'File "' + f_name + '"'
        if line != -1:
            if full_mess:
                full_mess += ', '
            full_mess += 'line '+str(line)
        if full_mess:
            full_mess += '\n'
        full_mess += mess
        if example != '':
            full_mess += '('+example+')'
        self.print_message(full_mess)

    def report_counter(self, fname, counter, vname):
        if not counter:
            return
        if fname is None:
            return
        self.try_create_folder(fname)
        try:
            with open(fname, 'w') as f_count:
                for data in counter.most_common():
                    f_count.write('{0}:{1} {2}\n'.format(data[0], data[1], vname))
        except Exception:
            self.fatal_error("can't write {0}\n".format(fname))

    def report(self):
        if self.wrong_docs:
            mess = "errors found in {0} documents.\n".format(sum(self.wrong_docs.values()))
            sys.stdout.write(mess)
            if self.err_report is not sys.stdout:
                self.err_report.write(mess)
                sys.stdout.write('See ' + self.err_report_name+'\n')
            self.report_counter(self.show_files_name, self.wrong_docs, 'error(s)')
        self.report_counter(self.stat_name, self.mess_counter, 'time(s)')
