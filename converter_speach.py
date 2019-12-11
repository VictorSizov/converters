# -*- Encoding: utf-8 -*-
"""
ConverterSpeach - конвертер xml-документов для устного корпуса.
"""

import re
import os

from lxml import etree
from lxml_ext import LxmlExt

from converter_basic import ConverterWithSteps, fill_arg_for_converter

SIMPLE_ACCENT = "`"
COMBINING_GRAVE_ACCENT = u'\u0300'  # ◌̀
COMBINING_ACUTE_ACCENT = u'\u0301'  # ◌́
COMBINING_CIRCUMFLEX_ACCENT = u'\u0302'  # ◌̂́


def escape_xml_text(s):
    return s.replace(u'&', u'&amp;').replace(u'<', u'&lt;').replace(u'>', u'&gt;')


# code from speach-cleaner.py end


class ConverterSpeach(ConverterWithSteps):

    def __init__(self, args):
        self.empty_actor = False
        super(ConverterSpeach, self).__init__(args)

    @staticmethod
    def get_steps():
        return 12

    @staticmethod
    def lowercase_attrib(body):
        for speech in body.iter('speech'):
            tmp = {key.lower(): value for key, value in speech.attrib.iteritems()}
            tmp = sorted(tmp.items())
            speech.attrib.clear()
            speech.attrib.update(tmp)

    @staticmethod
    def speach2speech(body):
        for speach in body.iter('speach'):
            speach.tag = 'speech'

    # <p sp="..." [speaker="..."]>   --->  <speech ...>
    def convert_p_sp(self, body):
        name = os.path.basename(self.inpname)
        for p in body.iter('p'):
            attr = p.attrib
            sp = attr.get('sp', None)
            if sp is not None:
                # атрибут sp: если nestand то"role[/actor]"  иначе "actor"
                sp_spl = [s.strip() for s in sp.split('/')]
                nestand = name in ['beloe_solnce.xhtml', 'zerkalo.xhtml']
                if nestand and len(sp_spl) == 2:
                    new_attr = {'role': sp_spl[0], 'actor': sp_spl[1]}
                else:
                    if len(sp_spl) != 1:
                        self.err_proc("'sp' has 2 values")
                        continue
                    new_attr = {'actor': sp} if not nestand else {'role': sp}
                # speaker: "<sex>|?,<age>|?,<profession>|?", ? - неизвестно
                speaker_str = attr.get('speaker', None)
                if speaker_str is not None:  # speaker есть
                    if len(attr) != 2:
                        self.err_proc("'p' with 'sp' and 'speaker' has extra attributes")
                        continue
                    data = [s.strip() for s in speaker_str.split(',')]

                    if len(data) != 3:  # обработка документов с нестандартным форматом или сообщение об ошибке
                        if name == u'shnur-zemfira.xhtml' and sp == u'Шнур-муж':
                            new_attr = {'actor': u"Шнур", 'sex': u'муж', 'profession': u'певец'}
                        elif name == 'zerkalo.xhtml':
                            new_attr['sex'] = data[0]
                        else:
                            self.err_proc("'speaker' should contain 3 elements")
                            continue
                    else:
                        for k, v in zip(['sex', 'age', 'profession'], data):
                            if v != '?':
                                new_attr[k] = v
                elif len(attr) != 1:
                    self.err_proc("'p' with 'sp has extra attributes")
                    continue
                # замена <p sp="..."> на сгенерированный <speech>
                p.tag = 'speech'
                p.attrib.clear()
                p.attrib.update(new_attr)
                # удаление тэга <b>
                for se in p.iter('se'):
                    self.line = se.sourceline
                    for child in se.iterchildren('b'):
                        se.text += child.tail
                        se.remove(child)
                    self.line = -1

    def get_val(self, attrib, key):
        # type: (dict, unicode) -> unicode
        value = attrib.get(key, None)
        if value is not None and (value == '' or value.isspace()):
            if key == 'actor':
                if not self.empty_actor:
                    self.err_proc("actor attribute is empty string")
                self.empty_actor = True
            else:
                del attrib[key]
                return None
        return value

    def convert_role2actor(self, root):
        is_kino = '/kino/' in self.inpname or '/theater/' in self.inpname \
                 or '/reading/' in self.inpname
        for speech in root.iter('speech'):
            self.line = speech.sourceline
            actor = self.get_val(speech.attrib, 'actor')
            role = self.get_val(speech.attrib, 'role')
            if actor is None and role is None:
                self.err_proc("speech tag hasn't actor and role attributes")
            if not is_kino:
                if actor is not None and actor != '' and role is not None:
                    self.err_proc(
                        "tag speach in non-cinema/theater/reading document has 'role' and 'actor' attribute ")
                    continue
                if role is not None:
                    speech.attrib['actor'] = role
                    del speech.attrib['role']

    @staticmethod
    def is_span_or_noindex(elem):
        return elem.tag == 'span' or elem.tag == 'noindex'

    @staticmethod
    def correct_lt_gt(text):
        if text is None:
            return None
        if text.find('<noindex>') == -1 and text.find('<distinct ') == -1:
            return None
        text = text.replace(u'&', u'&amp;').replace(u'<', u'&lt;').replace(u'>', u'&gt;')
        (text, nom) = re.subn(ur'&lt;(/?noindex|distinct\s*form\s*=\s*".*?"|/distinct)&gt;', ur'<\1>', text)
        if nom == 0:
            return None
        text = '<root>' + text + '</root>'
        # obtain tree with added tags
        elem = etree.fromstring(text)
        return elem

    def convert_lt_gt(self, body):
        for elem in body.iter():
            if elem.tag is etree.PI or elem.tag is etree.Comment:
                continue
            self.line = elem.sourceline
            res = self.correct_lt_gt(elem.text)
            if res is not None:
                elem.text = res.text
                self.insert_distinct_nrzb(elem, 0, res)
            res = self.correct_lt_gt(elem.tail)
            if res is not None:
                elem.tail = res.text
                parent = elem.getparent()
                self.insert_distinct_nrzb(parent, parent.index(elem) + 1, res)
            self.line = -1

    # для <span class="note"> или <noindex>   need_convert = false
    @staticmethod
    def correct_distinct_nrzb(text):
        if text is None:
            return None
        text0 = text
        text = re.sub(ur"(?:\[|{|&lt;|<)?нрзбр?ч?\.*(?:\}|&gt;|\]|>)?", u'[нрзб]', text)
        if text0 != text:
            pass
        need_convert = False
        if text.find('{') != -1 or text.find(u'[нрзб]') != -1:
            # escape special characters before possible add tags
            text = text.replace(u'&', u'&amp;').replace(u'<', u'&lt;').replace(u'>', u'&gt;')
            if text.find('{') != -1:
                # try to convert  X{Y}* to <distinct form="X">Y</distinct>
                (text, nom) = re.subn(ur"([а-яa-z◌́]+)\s*{(.*?)\*\}", ur'<distinct form="\1">\2</distinct>', text)
                if nom > 0:
                    need_convert = True
            else:
                text = text.replace(u"[нрзб]", u'<noindex>[нрзб]</noindex>')
                need_convert = True
        if not need_convert:
            return None
        text = '<root>' + text + '</root>'
        # obtain tree with added tags
        elem = etree.fromstring(text)
        return elem

    @staticmethod
    def insert_distinct_nrzb(parent, index, new_elem):
        for new_child in new_elem:
            parent.insert(index, new_child)
            index += 1

    def convert_distinct_nrzb(self, body):
        for elem in body.iter():
            if elem.tag is etree.PI or elem.tag is etree.Comment or elem.tag == 'w':
                continue
            if not self.is_span_or_noindex(elem):
                res = self.correct_distinct_nrzb(elem.text)
                if res is not None:
                    elem.text = res.text
                    self.insert_distinct_nrzb(elem, 0, res)
                res = self.correct_distinct_nrzb(elem.tail)
                if res is not None:
                    elem.tail = res.text
                    parent = elem.getparent()
                    self.insert_distinct_nrzb(parent, parent.index(elem) + 1, res)

    @staticmethod
    def is_empty(text):
        return text is None or text == '' or text.isspace()

    @classmethod
    def remove_spaces_txt(cls, text):
        if text is None:
            return None
        text = text.replace('  ', ' ')
        '''
        if text.isspace():
            n = text.count('\n')
            if n == 0:
                return text
            if n > 2:
                n = 2
            if n == 0:
                return None
            return '\n' * n
            '''
        return text

    def remove_spaces(self, body):
        for elem in body.iter():
            self.line = elem.sourceline
            elem.text = self.remove_spaces_txt(elem.text)
            elem.tail = self.remove_spaces_txt(elem.tail)

    def fix_accent(self, text, count):
        if text is None:
            return text, count
        text = text.replace(SIMPLE_ACCENT, COMBINING_ACUTE_ACCENT). \
            replace(COMBINING_GRAVE_ACCENT, COMBINING_ACUTE_ACCENT). \
            replace(COMBINING_CIRCUMFLEX_ACCENT, COMBINING_ACUTE_ACCENT)
        pos0 = 0
        vowels = u'аеиоуыэюяАЕИОУЫЭЮЯ'
        while True:
            pos = text.find(COMBINING_ACUTE_ACCENT, pos0)
            if pos == -1:
                break
            if pos == 0 or (text[pos - 1] not in vowels):
                if pos == len(text) - 1 or text[pos + 1] not in vowels:
                    self.err_proc("wrong accent")
                else:
                    tail = text[pos + 2:] if len(text) > pos + 2 else ''
                    text = text[:pos] + text[pos + 1] + COMBINING_ACUTE_ACCENT + tail
                    count += 1
            pos0 = pos + 2
        return text, count

    def fix_accents(self, body):
        is_manual = 'manual' in self.inpname
        if not is_manual:
            return
        count = 0
        for elem in body.iter():
            self.line = elem.sourceline
            elem.text, count = self.fix_accent(elem.text, count)
            elem.tail, count = self.fix_accent(elem.tail, count)
        if count > 10:
            self.err_proc("accent correction more then " + str(count))

    def try_convert_to_span(self, p_elem):
        if p_elem.get("class", '') in ('h1', 'footnote', 'h2', 'H1', 'H2') or \
                not p_elem.attrib and len(p_elem) == 0 and self.is_comment(p_elem.text):
            # todo диагностика если elem.text.isspace()==True
            p_elem.tag = 'span'
            p_elem.attrib.clear()
            p_elem.attrib['class'] = 'note'

    @staticmethod
    def is_comment(text):  # todo  check!
        return text in ["***"]

    def process_nonempty_texts1(self, body):
        elem_list = list(body)

        for elem in elem_list:
            if elem.tag is etree.PI or elem.tag is etree.Comment:
                continue
            #
            if elem.tag == 'p':
                class_attr = elem.get("class", '')
                if class_attr in ('h1', 'footnote', 'h2', 'H1', 'H2') or \
                        not elem.attrib and len(elem) == 0 and self.is_comment(elem.text):
                    span_attr = 'explain' if class_attr == 'footnote' else 'head'
                    # todo диагностика если elem.text.isspace()==True
                    elem.tag = 'span'
                    elem.attrib.clear()
                    elem.attrib['class'] = span_attr
                # todo диагностика  необычных атрибутов
                elif not elem.attrib:
                    # todo диагностика если elem.text/tail не isspace, не is_informative и не is_comment
                    is_informative = LxmlExt.is_informative(elem.text)
                    for descendant in elem.iter():
                        if descendant is elem:
                            continue
                        if LxmlExt.is_informative(descendant.tail) or not self.is_span_or_noindex(descendant) and \
                                LxmlExt.is_informative(descendant.text):
                            is_informative = True
                    if is_informative:
                        elem.tag = 'speech'
                    elif self.is_empty(elem.text):
                        LxmlExt.disband_node(elem)

    def process_nonempty_texts2(self, body):
        elem_list = list(body)
        if LxmlExt.is_informative(body.tail):
            LxmlExt.surround_tail(body, etree.Element("speech"))

        for elem in elem_list:
            if elem.tag is etree.PI or elem.tag is etree.Comment:
                continue
            #
            if elem.tag == 'p':
                if elem.attrib.get("class", '') == "verse":
                    LxmlExt.surround_node(elem, etree.Element("speech"))
            if elem.tag == 'se' and len(elem) > 0:
                prev = elem.getprevious()
                if prev is not None and prev.tag == 'speech':
                    LxmlExt.move_element_into(elem, prev)
                else:
                    LxmlExt.surround_node(elem, etree.Element("speech"))
            if elem.tag == 'speech':
                if LxmlExt.is_informative(elem.tail):
                    LxmlExt.surround_tail(elem, etree.Element("speech"))
            if self.is_span_or_noindex(elem):
                if LxmlExt.is_informative(elem.tail):
                    if elem.tag == 'span ' and elem.attrib.get('class', '') == 'head':
                        LxmlExt.surround_tail(elem, etree.Element("speech"))
                    else:
                        LxmlExt.surround_node(elem, etree.Element("speech"))
            if elem.tag == 'br' or elem.tag == 'distinct':
                prev = elem.getprevious()
                if prev is not None and prev.tag == 'speech':
                    LxmlExt.move_element_into(elem, prev)

    @classmethod
    def get_text(cls, elem, is_ancestor=False):
        text = elem.text
        n = len(elem)
        for child in elem:
            text = LxmlExt.concat_text(text, cls.get_text(child))
            elem.remove(child)
            n -= 1
        if len(elem) > 0:
            raise Exception("Logic error")
        if not is_ancestor:
            text = LxmlExt.concat_text(text, elem.tail)
        return text

    @classmethod
    def process_span_noindex_text(cls, body):
        sp_list = [elem for elem in body.iter('span', 'noindex')]
        for elem in sp_list:
            if elem.getparent() is None:  # напр <noindex> внутри <span> может стереться, его нет смысла рассматривать
                continue
            if len(elem) == 0:
                continue
            text = cls.get_text(elem, True)
            text = text.lstrip().rstrip()
            text = text.replace(COMBINING_ACUTE_ACCENT, '').replace('\n', ' ').replace('  ', ' ')
            elem.text = text

    @staticmethod
    def process_p_note(body):
        for p in body.iter('p'):
            if p.attrib.get('class', '') == 'note':
                p.tag = 'span'

    def process_lxml_tree(self, tree):
        root = tree.getroot()
        body = root.find('body')
        if body is None:
            raise etree.LxmlError("<body> tag not found")
        if self.check_steps(0):
            self.lowercase_attrib(body)
        if self.check_steps(1):
            self.convert_p_sp(body)
        if self.check_steps(2):
            self.speach2speech(body)
        if self.check_steps(3):
            self.empty_actor = False
            self.convert_role2actor(body)
        if self.check_steps(4):
            self.convert_lt_gt(body)
        if self.check_steps(5):
            self.convert_distinct_nrzb(body)
        if self.check_steps(6):
            self.remove_spaces(root)
        if self.check_steps(7):
            self.fix_accents(body)
        if self.check_steps(8):
            self.process_nonempty_texts1(body)
        if self.check_steps(9):
            self.process_nonempty_texts2(body)
        if self.check_steps(10):
            self.process_p_note(body)
        if self.check_steps(11):
            self.process_span_noindex_text(body)


if __name__ == '__main__':
    parser = fill_arg_for_converter('speech converter')
    parser.add_argument('--step_mode', type=int, default=ConverterSpeach.get_steps())
    parser_args = parser.parse_args()
    converter = ConverterSpeach(parser_args)
    converter.process()
