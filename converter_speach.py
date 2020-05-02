# -*- Encoding: utf-8 -*-
"""
ConverterSpeach - конвертер xml-документов для устного корпуса.
"""

import re
import os

from lxml import etree
from lxml_ext import LxmlExt

from converter_basic import ConverterWithSteps, fill_arg_for_converter
SIMPLE_APOSTROPHE = "'"   # code: 39, 0x27
SIMPLE_ACCENT = "`"  # code: 96, 0x60
COMBINING_GRAVE_ACCENT = u'\u0300'  # ◌̀
COMBINING_ACUTE_ACCENT = u'\u0301'  # ◌́
COMBINING_CIRCUMFLEX_ACCENT = u'\u0302'  # ◌̂́
RIGHT_SINGLE_QUOTATION_MARK = u'\u2019'  # ’

sex_values = {u'муж', u'жен', u'муж-жен', u'жен-муж'}
prof_values = {
    u'студент',
    u'инженер',
    u'пенсионер',
    u'журналист',
    u'безработный',
    u'футболист',
    u'работник торговли',
    u'военный',
    u'администратор',
    u"библиотекарь",
    u'массажистка',
    u'музыкант',
    u'медработник',
    u'студентка',
    u'ученый',
    u'священник',
    u'лингвист',
    u'служащий',
    u'преподаватель',
    u'продавец',
    u"замдиректора образовательного центра",
    u'режиссер',
    u'маячник',
    u'медсестра',
    u'чтец',
}

sex_correct = {
    u"мужской": u"муж",
    u"женский": u"жен",
    u"муж/жен": u"муж-жен",
    u"же": u"жен",
    u"уж": u"муж",
    u"жн": u"жен",
    u"мкж-жен": u"муж-жен",
    u'муж? / ?': u"муж",
    u'муж / ? / ?': u"муж",
    u'муж?': u"муж",
    u'? / муж': u"муж",
    u'муж+?': u"муж",
    u'-жен': u"жен",
    u'жен.': u"жен",
    u'муж.': u"муж",
    u'жен / ? / ?': u"жен",
    u'му': u"муж",
    u'жен / ? / ': u"жен",
    u'муж+': u"муж",
    u'муж|жен': u'муж-жен',
    u'жён': u'жен'
}

age_correct = {
    u"20лет": u"20",
    u"22студент": u"22-студент",
    u"19 студент": u"19-студент",
}


def escape_xml_text(s):
    return s.replace(u'&', u'&amp;').replace(u'<', u'&lt;').replace(u'>', u'&gt;')


# code from speach-cleaner.py end


class ConverterSpeach(ConverterWithSteps):

    re_space = re.compile(ur'   *')

    def __init__(self, args):
        members_list = [self.lowercase_attrib,  # 0
                        self.convert_p_sp,  # 1
                        self.speach2speech,  # 2
                        self.convert_role2actor,  # 3
                        self.convert_lt_gt,  # 4
                        self.convert_distinct_nrzb,  # 5
                        self.remove_spaces,  # 6
                        self.fix_accents,  # 7
                        self.process_nonempty_texts1,  # 8
                        self.process_nonempty_texts2,  # 9
                        self.process_p_note,  # 10
                        self.process_span_noindex_text,  # 11
                        self.process_one_attr_correct,  # 12
                        self.process_mix_attrs_correct,  # 13
                        self.space_after_distinct,  # 14
                        ]
        self.members_dict = {key: value for key, value in enumerate(members_list)}
        super(ConverterSpeach, self).__init__(args)

    @staticmethod
    def get_steps():
        return 15

    def get_step_methods(self):
        return self.members_dict

    def lowercase_attrib(self, root):
        for speech in root.iter('speech'):
            to_lower = False
            tmp = dict()
            # tmp = {key.lower(): value for key, value in speech.attrib.iteritems()}
            for key, value in speech.attrib.iteritems():
                lower_key = key.lower()
                if lower_key != key:
                    self.count_mess('<speech>: to_lower ' + key)
                    to_lower = True
                tmp[lower_key] = value
            if to_lower:
                tmp = sorted(tmp.items())
                speech.attrib.clear()
                speech.attrib.update(tmp)

    def speach2speech(self, root):
        for speach in root.iter('speach'):
            speach.tag = 'speech'
            self.count_mess('<speach> -> <speech>')

    # <p sp="..." [speaker="..."]>   --->  <speech ...>
    def convert_p_sp(self, root):
        body = root.find('body')
        name = os.path.basename(self.inpname)
        for p in body.iter('p'):
            attr = p.attrib
            self.line = p.sourceline
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
                    self.count_mess('speaker ->  age/birth/sex/profession')
                elif len(attr) != 1:
                    self.err_proc("'p' with 'sp has extra attributes")
                    continue
                new_attr = sorted(new_attr.items())
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
                self.count_mess('sp -> actor/role')

    @staticmethod
    def check_empty_attr(attrib, key):
        value = attrib.get(key, None)
        return value is None or value == '' or value.isspace()

    def get_attr_val(self, elem, key):
        # type: (etree.Element, unicode) -> [unicode, None]
        value = elem.attrib.get(key, None)
        if value is not None and (value == '' or value.isspace() or value == '?'):
            if key != 'actor':
                self.count_mess("<speech>: delete empty attribute " + key)
                del elem.attrib[key]
                return None
            else:
                elem.attrib[key] = ''
                return ''
        return value

    def convert_role2actor(self, root):
        is_kino = '/kino/' in self.inpname or '/theater/' in self.inpname \
                 or '/reading/' in self.inpname
        for speech in root.iter('speech'):
            self.line = speech.sourceline
            actor = self.get_attr_val(speech, 'actor')
            role = self.get_attr_val(speech, 'role')
            if not is_kino:
                if role is not None and self.is_empty(actor):
                    speech.attrib['actor'] = role
                    del speech.attrib['role']
                    self.count_mess("<speech>: role -> actor")
                    tmp = sorted(speech.attrib.items())
                    speech.attrib.clear()
                    speech.attrib.update(tmp)

    @staticmethod
    def is_span_or_noindex(elem):
        return elem.tag == 'span' or elem.tag == 'noindex'

    def correct_lt_gt(self, text):
        if text is None:
            return None
        if text.find('<noindex>') == -1 and text.find('<distinct ') == -1:
            return None
        text = text.replace(u'&', u'&amp;').replace(u'<', u'&lt;').replace(u'>', u'&gt;')
        (text, nom) = re.subn(ur'&lt;(/?noindex|distinct\s*form\s*=\s*".*?"|/distinct)&gt;', ur'<\1>', text)
        if nom == 0:
            return None
        self.count_mess("restore encoded tags &lt;noindex|distinct&gt; to standard", nom)
        text = '<root>' + text + '</root>'
        # obtain tree with added tags
        elem = etree.fromstring(text)
        return elem

    def convert_lt_gt(self, root):
        body = root.find('body')
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

    def correct_distinct_nrzb(self, text):
        if text is None:
            return None
        text0 = text
        (text, nom) = re.subn(ur"(?:\[|{|&lt;|<)?нрзбр?ч?\.*(?:\}|&gt;|\]|>)?", u'[нрзб]', text)
        if nom > 0:
            self.count_mess('normalization of [нрзб]')
        need_convert = False
        if text.find('{') != -1 or text.find(u'[нрзб]') != -1:
            # escape special characters before possible add tags
            text = text.replace(u'&', u'&amp;').replace(u'<', u'&lt;').replace(u'>', u'&gt;')
            if text.find('{') != -1:
                # try to convert  X{Y}* to <distinct form="X">Y</distinct>
                (text, nom) = re.subn(ur"([\-ёЁА-Яа-яA-Za-z◌́]+)\s*{\*?(.*?)\*?}", ur'<distinct form="\1">\2</distinct>', text)
                if nom > 0:
                    self.count_mess('conversion of  X{Y}* to <distinct form="X">Y</distinct>',nom)
                    need_convert = True
            if text.find(u'[нрзб]') != -1:
                # todo проверить что вокруг [нрзб] нет <noindex>
                text = text.replace(u"[нрзб]", u'<noindex>[нрзб]</noindex>')
                self.count_mess('conversion of  [нрзб] to <noindex>[нрзб]</noindex>')
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

    def convert_distinct_nrzb(self, root):
        body = root.find('body')
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

    def replace(self, src, dest, text):
        text_n = text.replace(src, dest)
        if text != text_n:
            self.count_mess('replacing \"' + src + '\" to \"' + dest + '\"')
        return text_n

    def remove_spaces_txt(self, text):
        if text is None:
            return None
        if text.find('  ') == -1:
            return text
        (text, count) = self.re_space.subn(' ', text)
        if count > 0:
            self.count_mess('extra space removed')
        return text

    def remove_spaces(self, root):
        body = root.find('body')
        for elem in body.iter():
            self.line = elem.sourceline
            elem.text = self.remove_spaces_txt(elem.text)
            elem.tail = self.remove_spaces_txt(elem.tail)

    def fix_accent(self, text, count, is_manual):
        if text is None:
            return text, count
        vowels = u'аеиоуыэюяАЕИОУЫЭЮЯ'
#        text = self.replace(COMBINING_GRAVE_ACCENT, COMBINING_ACUTE_ACCENT, text)
        text = self.replace(COMBINING_CIRCUMFLEX_ACCENT, COMBINING_ACUTE_ACCENT, text)
        text = self.replace(RIGHT_SINGLE_QUOTATION_MARK, COMBINING_ACUTE_ACCENT, text)


        if text.find("'") != -1:
            text = text.replace(u"а'", u'а\u0301').replace(u"е'", u'е\u0301').replace(u"и'", u'и\u0301')
            text = text.replace(u"у'", u'у\u0301').replace(u"э'", u'э\u0301').replace(u"ю'", u'ю\u0301')
            text = text.replace(u"я'", u'я\u0301').replace(u"ы'", u'ы\u0301').replace(u"о'", u'о\u0301')
        if not is_manual:
            text = self.replace(SIMPLE_ACCENT, COMBINING_GRAVE_ACCENT, text)

            return text, count
        text = self.replace(SIMPLE_ACCENT, COMBINING_ACUTE_ACCENT, text)
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

    def fix_accents(self, root):
        body = root.find('body')
        is_manual = 'manual' in self.inpname or 'main/standard' in self.inpname
        count = 0
        for elem in body.iter():
            if elem.tag is etree.PI or elem.tag is etree.Comment:
                continue
            self.line = elem.sourceline
            elem.text, count = self.fix_accent(elem.text, count, is_manual)
            elem.tail, count = self.fix_accent(elem.tail, count, is_manual)
            if elem.tag == 'distinct':
                elem.attrib['form'] = elem.get('form', '').replace(SIMPLE_APOSTROPHE, COMBINING_ACUTE_ACCENT)

        if count > 0:
            self.count_mess('accent moved', count)

    @staticmethod
    def is_comment(text):  # todo  check!
        return text in ["***"]

    def process_nonempty_texts1(self, root):
        body = root.find('body')
        elem_list = list(body)

        for elem in elem_list:
            if elem.tag is etree.PI or elem.tag is etree.Comment:
                continue
            #
            if elem.tag == 'p':
                class_attr = elem.get("class", '')
                if class_attr in ('h1', 'footnote', 'h2', 'H1', 'H2') or \
                        not elem.attrib and len(elem) == 0 and self.is_comment(elem.text):
                    span_attr = 'note' if class_attr == 'footnote' else 'head'
                    # todo диагностика если elem.text.isspace()==True
                    elem.tag = 'span'
                    elem.attrib.clear()
                    elem.attrib['class'] = span_attr
                    self.count_mess('<p> -> <span>')
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
                        self.count_mess('<p> -> <speech>')
                    elif self.is_empty(elem.text):
                        LxmlExt.disband_node(elem)
                        self.count_mess('clear <p>')

    def process_nonempty_texts2(self, root):
        body = root.find('body')
        elem_list = list(body)
        if LxmlExt.is_informative(body.tail):
            LxmlExt.surround_tail(body, etree.Element("speech"))
            self.count_mess('put outbound text into <speech> tag')

        for elem in elem_list:
            if elem.tag is etree.PI or elem.tag is etree.Comment:
                continue
            #
            if elem.tag == 'p':
                if elem.attrib.get("class", '') == "verse":
                    LxmlExt.surround_node(elem, etree.Element("speech"))
                    self.count_mess('put outbound text into <speech> tag')
            if elem.tag == 'se' and len(elem) > 0:
                prev = elem.getprevious()
                if prev is not None and prev.tag == 'speech':
                    LxmlExt.move_element_into(elem, prev)
                else:
                    LxmlExt.surround_node(elem, etree.Element("speech"))
                self.count_mess('put outbound text into <speech> tag')
            if elem.tag == 'speech':
                if LxmlExt.is_informative(elem.tail):
                    LxmlExt.surround_tail(elem, etree.Element("speech"))
                    self.count_mess('put outbound text into <speech> tag')
            if self.is_span_or_noindex(elem):
                if LxmlExt.is_informative(elem.tail):
                    if elem.tag == 'span ' and elem.attrib.get('class', '') == 'head':
                        LxmlExt.surround_tail(elem, etree.Element("speech"))
                    else:
                        LxmlExt.surround_node(elem, etree.Element("speech"))
                    self.count_mess('put outbound text into <speech> tag')
            if elem.tag == 'br' or elem.tag == 'distinct':
                prev = elem.getprevious()
                if prev is not None and prev.tag == 'speech':
                    LxmlExt.move_element_into(elem, prev)
                self.count_mess('put outbound text into <speech> tag')
        for speech in body.iter('speech'):
            if self.is_empty(speech.text) and not speech.attrib and len(speech) == 1 and speech[0].tag == 'br':
                if self.is_empty(speech.tail):
                    speech.getparent().remove(speech)
                else:
                    speech.remove(speech[0])
                    LxmlExt.disband_node(speech)
                self.count_mess('put outbound text into <speech> tag')

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

    def process_span_noindex_text(self, root):
        body = root.find('body')
        sp_list = [elem for elem in body.iter('span', 'noindex')]
        for elem in sp_list:
            if elem.getparent() is None:  # напр <noindex> внутри <span> может стереться, его нет смысла рассматривать
                continue
            if len(elem) == 0:
                continue
            text = self.get_text(elem, True)
            text = text.lstrip().rstrip()
            text = text.replace(COMBINING_ACUTE_ACCENT, '').replace('\n', ' ').replace('  ', ' ')
            self.count_mess('clear elements in <'+elem.tag+'>')
            elem.text = text

    def process_p_note(self, root):
        body = root.find('body')
        for p in body.iter('p'):
            if p.attrib.get('class', '') == 'note':
                p.tag = 'span'
                self.count_mess('<p class="note"> -> <span class "note"')

    def process_one_attr_correct(self, root):
        body = root.find('body')
        for speech in body.iter('speech'):
            change = False
            for key in speech.attrib.keys():
                val_old = self.get_attr_val(speech, key)
                if val_old is None or val_old == '':
                    continue
                val = val_old
                if key == 'sex':
                    val_n = sex_correct.get(val, None)
                    if val_n is not None:
                        val = val_n
                if key == 'age':
                    val_n = age_correct.get(val, None)
                    if val_n is not None:
                        val = val_n
                if key not in ['actor', 'role'] and val[-1] in '?.':
                    val = val[:-1]
                if val != val_old:
                    speech.attrib[key] = val
                    self.count_mess(key + ': "' + val_old + '" -> "' + val + '"')
                    change = True
            if change:
                tmp = sorted(speech.attrib.items())
                speech.attrib.clear()
                speech.attrib.update(tmp)

    @staticmethod
    def guess_one(value):
        if value in sex_values:
            return 'sex'
        if value in prof_values:
            return 'profession'
        try:
            val = int(value)
        except ValueError:
            return 'NO_SWAP'
        if 1 < val <= 100:
            return 'age'
        if 1750 < val < 2019:
            return 'birth'
        return 'NO_SWAP'

    @classmethod
    def guess_diap(cls, values):
        if len(values) != 2:
            return 'NO_SWAP'
        res0 = cls.guess_one(values[0])
        res1 = cls.guess_one(values[1])
        if res0 != res1 or res0 not in ['age', 'birth']:
            return 'NO_SWAP'
        return res0

    @classmethod
    def guess_group(cls, values):
        ret = dict()
        for value in values:
            res = cls.guess_one(value)
            if res == 'NO_SWAP':
                res = cls.guess_diap(value.split('-'))
            if res == 'NO_SWAP':
                return {'NO_SWAP': None}
            if res in ret:
                return {'NO_SWAP': None}
            else:
                ret[res] = value
        return ret

    @classmethod
    def guess_value(cls, value):
        ret = cls.guess_one(value)
        if ret != 'NO_SWAP':
            return {ret: value}
        values = value.split('/')
        if len(values) == 1:
            values = value.split('-')
            if len(values) == 1:
                return {'NO_SWAP': None}
            ret = cls.guess_diap(values)
            if ret != 'NO_SWAP':
                return {ret: value}
        values = [v.strip() for v in values if v.strip() not in ['?', '']]
        if len(values) > 4:
            return {'NO_SWAP': None}
        return cls.guess_group(values)

    def form_dict(self, elem, key, prop_dict):
        rel_dict = dict()
        attr_type = 'EMPTY'
        value = self.get_attr_val(elem, key)
        if value is not None:
            rel_dict = self.guess_value(value)
            if 'NO_SWAP' in rel_dict:
                attr_type = 'NO_SWAP'
                rel_dict = {}
            elif key in rel_dict:
                if len(rel_dict) == 1:
                    attr_type = 'CORRECT'
                    rel_dict = {}
        prop_dict[key] = [attr_type, value, rel_dict]

    def swap_report(self, prop_dict, before_filters):
        continue_work = False
        for key, value in prop_dict.iteritems():
            attr_type = value[0]
            attr_value = value[1]
            swap_dict = value[2]
            if swap_dict:
                if before_filters:
                    return True
                continue_work = True
                mess = key + ' -> '
                sep = ''
                for key_swap in set(swap_dict.keys()):
                    mess += sep
                    mess += key_swap
                    sep = ' + '
                self.count_mess(mess)
        return continue_work

    def process_mix_attrs_correct(self, root):
        body = root.find('body')
        for speech in body.iter('speech'):
            prop_dict = dict()
            attrib = dict(speech.attrib)
            self.form_dict(speech, 'age', prop_dict)
            self.form_dict(speech, 'birth', prop_dict)
            self.form_dict(speech, 'sex', prop_dict)
            self.form_dict(speech, 'profession', prop_dict)
            attrib = dict(speech.attrib)
            continue_work = self. swap_report(prop_dict, True)
            if not continue_work:
                continue
            while continue_work:
                continue_work = False
                for key, value in prop_dict.items():
                    attr_type = value[0]
                    attr_value = value[1]
                    swap_dict = value[2]
                    reset_swap = False
                    for key_swap, value_swap in swap_dict.items():
                        dest_value = prop_dict[key_swap]
                        if dest_value[0] == 'CHANGE':
                            if value_swap != dest_value[1]:
                                dest_value[0] = 'MULTIPLE'
                        if dest_value[0] == 'EMPTY':
                            dest_value[0] = 'CHANGE'
                            dest_value[1] = value_swap
                        if dest_value[0] != 'CHANGE':
                            if dest_value[0] == 'EMPTY':
                                raise Exception("Logic error")
                            if dest_value[0] == 'MULTIPLE' or value_swap != dest_value[1]:
                                if not reset_swap:
                                    attr_type = 'NO_SWAP'
                                    attr_value = attrib[key]
                                    self.count_mess('reject ' + key + ' -> ' + key_swap)
                                    reset_swap = True
                                else:
                                    self.count_mess('ignore ' + key + ' -> ' + key_swap)
                            del swap_dict[key_swap]

                    if reset_swap:
                        prop_dict[key] = [attr_type, attr_value, swap_dict]
                        continue_work = True

            continue_work = self.swap_report(prop_dict, False)
            if not continue_work:
                continue
            for key, value in prop_dict.items():
                attr_type = value[0]
                attr_value = value[1]
                if attr_type == 'CHANGE':
                    speech.attrib[key] = attr_value
                if attr_type == 'EMPTY':
                    if key in speech.attrib:
                        del speech.attrib[key]
            tmp = sorted(speech.attrib.items())
            speech.attrib.clear()
            speech.attrib.update(tmp)

    def space_after_distinct(self, root):
        for distinct in root.iter('distinct'):
            if distinct.tail is None:
                continue
            if isinstance(distinct.tail, unicode):
                if unicode.isalnum(distinct.tail[0]):
                    distinct.tail = u' ' + distinct.tail
            elif isinstance(distinct.tail, str):
                if str.isalnum(distinct.tail[0]):
                    distinct.tail = ' ' + distinct.tail
            else:
                print distinct.tail
                raise Exception("logic error")


if __name__ == '__main__':
    parser = fill_arg_for_converter('speech converter')
    parser.add_argument('--step_mode', default=str(-1))
    parser_args = parser.parse_args()
    converter = ConverterSpeach(parser_args)
    converter.process()
