# -*- Encoding: utf-8 -*-
"""
ConverterBasic - базовый класс для конвертера xml - документов.
ConverterWithSteps - базовый класс для отладочного "пошагового" конвертера xml - документов.
"""

from processor_basic import ProcessorBasic


class ConverterWithSteps(ProcessorBasic):
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
        return tree

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
            self.fatal_error(mess_prefix + 'step_mode wrong value')
        if step > self.get_steps():
            self.fatal_error(mess_prefix + 'step_mode is too big')
        return step


