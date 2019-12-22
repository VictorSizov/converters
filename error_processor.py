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
        self.stat_name = kwargs.get('stat', None)
        self.limit = kwargs.get('limit', -1)
        self.inppath = expanduser(kwargs['inppath'])

        self.err_report_name = expanduser(kwargs.get('err_report', None)) # имя файла для ошибок
        self.mess_counter = Counter() if self.stat_name is not None else None
        self.f_err_name = ''
        self.wrong_docs = 0
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
    def try_create(path):
        if path is None or path == '':
            return
        if not os.path.exists(path):
            os.makedirs(path)

    def open_log(self,):
        try:
            if self.err_report_name is None:
                self.err_report = sys.stderr
                sys.stdout = open(os.devnull, 'w')
            else:
                err_report_name = self.err_report_name
                if self.step != '':
                    (err_report_name, ext) = os.path.splitext(err_report_name)
                    err_report_name += str(self.step) + ext
                self.try_create(os.path.split(err_report_name)[0])
                self.err_report = open(err_report_name, 'w')
        except (OSError, IOError) as e:
            self.fatal_error("Can't open message file " + self.err_report_name)

    def load_ignore_mess(self):
        try:
            if self.ignore_mess_name is not None:
                with open(self.ignore_mess_name, 'r') as f:
                    self.ignore_mess=f.read().splitlines()
                self.ignore_mess_name = None
        except (OSError, IOError) as e:
            self.fatal_error("Can't load list of ignored messages " + self.ignore_mess_name)

    def print_message(self, mess):
        if self.err_report is None:  # если файл для вывода сообщения не проинициализирован
            self.open_log()
        if isinstance(mess, unicode):
            mess = mess.encode(encoding='utf-8')
        self.err_report.write(mess+'\n')
        self.err_num += 1
        if self.limit != -1 and self.limit <= self.err_num:
            self.fatal_error('Message number exceed '+str(self.limit))

    def check_ignore(self, mess):
        if isinstance(mess, unicode):
            mess = mess.encode('utf-8')
        return self.ignore_mess is not None and mess in self.ignore_mess

    def proc_message(self, mess, f_name=None, line=-1, example=''):
        if self.check_ignore(mess):
            return
        self.count_mess(mess)
        full_mess = ''
        if f_name is not None:
            if self.f_err_name != f_name:
                self.wrong_docs += 1
            self.f_err_name = f_name
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
        if self.wrong_docs > 0:
            mess = "errors found in {0} documents.\n".format(self.wrong_docs,)
            sys.stderr.write(mess)
            if self.err_report is not sys.stderr:
                self.err_report.write(mess)
                sys.stderr.write('See ' + self.err_report_name+'\n')
        if self.mess_counter:
            self.try_create(os.path.split(self.stat_name)[0])
            try:
                with open(self.stat_name, 'w') as f_count:
                    for err in self.mess_counter.most_common():
                        err_txt = err[0]
                        if isinstance(err_txt, unicode):
                            err_txt = err_txt.encode(encoding='utf-8')
                        f_count.write(err_txt + ': ' + str(err[1]) + ' time(s)\n')
            except Exception as e:
                self.fatal_error("can't write statistics into " + self.stat_name)
