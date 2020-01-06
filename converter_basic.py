# -*- Encoding: utf-8 -*-
"""
ConverterBasic - базовый класс для конвертера xml - документов.
ConverterWithSteps - базовый класс для отладочного "пошагового" конвертера xml - документов.
"""

from processor_basic import ProcessorBasic, fill_arg_for_processor, ProgramTerminated, expanduser
import os
import sys
from lxml import etree
import time


class ConverterBasic(ProcessorBasic):
    def __init__(self, args):
        self.outpath = expanduser(args.outpath)
        self.outcode = args.outcode
        super(ConverterBasic, self).__init__(args)

    def process_file(self, inpfile):
        """ Обработка xml - дерева и запись его
        в выходной файл в соответствующей кодировке"""
        tree = super(ConverterBasic, self).process_file(inpfile)
        if tree is None:
            return
        try:
            outpath = self.outpath if self.outpath is not None else self.inppath
            outfile = os.path.join(outpath, inpfile) if inpfile != '' else  outpath
            outdir = os.path.dirname(outfile)
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            with open(outfile, 'w') as fout:
                fout.write('<?xml version="1.0" encoding="{0}"?>\n'.format(self.outcode))
                tree.write(fout, encoding=self.outcode, xml_declaration=False)
        except (OSError, IOError) as e:
            self.fatal_error("can't write  output file " + outfile)
        except etree.LxmlError as e:
            self.lxml_err_proc(e)


class ConverterWithSteps(ConverterBasic):
    """пошаговый конвертер"""
    def __init__(self, args):
        super(ConverterWithSteps, self).__init__(args)
        self.step_list = self.get_step_list(args.step_mode)

    @staticmethod
    def get_steps():
        raise Exception('you should rewrite this function in derived class')

    def get_step_methods(self):
        raise Exception('you should rewrite this function in derived class')

    def process_lxml_tree(self, tree):
        self.line = -1
        root = tree.getroot()
        methods = self.get_step_methods()
        for n in self.step_list:
            methods[n](root)

    def get_step_list(self, step_mode):
        step_list = []
        if step_mode == '-1':
            step_list.extend(range(self.get_steps()))
            return step_list
        if step_mode[0] == ',' or step_mode [-1] == ',':
            self.fatal_error('step_mode {0} is wrong'.format(step_mode))
        for step1 in step_mode.split(','):
            if step1[0] == '-' or step1[-1] == '-':
                self.fatal_error('part of step_mode {0} is wrong'.format(step1))
            steps2 = step1.split('-')
            if len(steps2) > 2:
                self.fatal_error("part of step_mode {0} is wrong".format(step1))
            if len(steps2) == 2:
                step0 = self.check_step_str(steps2[0], 'lower bound of {0}'.format(step1))
                step1 = self.check_step_str(steps2[1], 'upper bound of {0}'.format(step1))
                step_list.extend(range(step0, step1))
            else:
                step_list.append(self.check_step_str(steps2[0]))
        prev = None
        for curr in step_list:
            if prev is not None and prev >= curr:
                self.fatal_error("list of actions {0} is wrong".format(self.step_list.__repr__()))
            prev = curr
        return step_list

    def check_step_str(self, step_str, mess_prefix=''):
        # type: (str, str) -> int
        try:
            step = int(step_str)
        except ValueError:
            self.fatal_error(mess_prefix + 'step_mode is not convertable to int')
        if step < -1 or mess_prefix != '' and step == -1:
            self.fatal_error( mess_prefix + 'step_mode wrong value')
        if step > self.get_steps():
            self.fatal_error(mess_prefix + 'step_mode is too big')
        return step


class Normalizer(ConverterBasic):
    def process_lxml_tree(self, tree):
        for elem in tree.getroot().iter():
            tmp = sorted(elem.items())
            elem.attrib.clear()
            elem.attrib.update(tmp)


def fill_arg_for_converter(description, action_description=None):
    parser = fill_arg_for_processor(description, action_description)
    parser.add_argument('--outpath', default=None)
    parser.add_argument('--outcode', choices=['utf-8', 'windows-1251'], default='utf-8')
    return parser


if __name__ == '__main__':
    parser = fill_arg_for_converter('normalizer')
    parser_args = parser.parse_args()
    normalizer = Normalizer(parser_args)
    normalizer.process()
