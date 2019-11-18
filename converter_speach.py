# -*- Encoding: utf-8 -*-

import re
import os
import sys
from lxml import etree

from converter_base import ConverterBase


# code from speach-cleaner.py begin
_charsRe = re.compile(ur"[а-яА-ЯA-Za-z]")


#_nrzbSrch = re.compile(ur"[^[](({)|(&lt;))?нрзбр?ч?\.?((})|(&gt;))[^\]]")
nrzbSrch = re.compile(ur"(?:^|[^[])(нрзб)(?:$|[^\]])")

def nrzb(stro):
    if stro is None:
        return stro
    return stro.replace(u"&lt;нрзб&gt;", u"<noindex>[нрзб]</noindex>").\
        replace(u"[нрзб]", u"<noindex>[нрзб]</noindex>").\
        replace(u"’", u"\u0301").replace(u"'", u"\u0301")


def _quotetext(s):
    if not s:
        return u""
    return s.replace(u'&', u'&amp;').replace(u'<', u'&lt;').replace(u'>', u'&gt;').replace(u'`', u'&#769;').replace(u"'", u'&#769;')


def _quoteattr(s):
    return _quotetext(s).replace(u"'", u'&#39;').replace(u'"', u'&#34;').replace(u'\n', u'&#xA;').replace(u'\r', u'&#xD;').replace(u'\t', u'&#x9;')
# code from speach-cleaner.py end


class ConverterSpeach(ConverterBase):
    def __init__(self, args):
        self.linestr=None
        ConverterBase.__init__(self, args)

    @staticmethod
    def lowercase_attrib(root):
        for speech in root.iter('speech'):
            tmp = {key.lower(): value for key, value in speech.attrib.iteritems()}
            speech.attrib.clear()
            speech.attrib.update(tmp)

    @staticmethod
    def speach2speech(root):
        for speach in root.iter('speach'):
            speach.tag = 'speech'

    # <p sp="..." [speaker="..."]>   --->  <speech ...>
    def convert_p_sp(self, root):
        name = os.path.basename(self.inpname)
        for p in root.iter('p'):
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

    @staticmethod
    def convert_noindex2span(root):
        for check_elem in root.iter('noindex'):
            check_elem.tag ='span'
            check_elem.attrib = {'class': 'note'}

    @staticmethod
    def get_val(attrib, key):
        # type: (dict, unicode) -> unicode
        value = attrib.get(key, None)
        if value is not None and (value == '' or value.isspace()):
            del attrib[key]
            return None
        return value

    def convert_role2actor(self, root):
        isKino = 'accent_main/texts/kino' in self.inpname or 'accent_main/texts/theater' in self.inpname \
                     or 'accent_main/texts/reading' in self.inpname
        for speech in root.iter('speech'):
            self.line = speech.sourceline
            actor = self.get_val(speech.attrib, 'actor')
            role = self.get_val(speech.attrib, 'role')
            if actor is None and role is None:
                self.err_proc("speech tag hasn't actor and role attributes")
            if not isKino:
                if actor is not None and role is not None:
                    self.err_proc(
                        "tag speach in non-cinema/theater/reading document has 'role' and 'actor' attribute ")
                    continue
                if role is not None:
                    speech.attrib['actor'] = role
                    del speech.attrib['role']


     # не должно вызываться для <span class="note">
    @staticmethod
    def correct_distinct_nrzb(text):
        need_convert = False
        if text is None:
            return None
        if text.find('{') != -1:  # {}* found, extra spaces deleting
            (text, nom) = re.subn(ur"([а-яa-z]+)\s*\{(.*?)\*\}",ur'<distinct form="\1">\2</distinct>',text)
            if nom > 0:
                need_convert = True
        if text.find(u'нрзб') != -1: # 'нрзб' found, normalizing it
            (text, nom) = re.subn(ur"(?:\[|\{|&lt;)?нрзбр?ч?\.?(?:\]|\}|&gt;)",u'<span class="note">[нрзб]</span>',text)
            if nom > 0:
                need_convert = True
        if not need_convert:
            return None
        text = '<root>'+text+'</root>'
        elem = etree.fromstring(text)
        return elem

    @staticmethod
    def insert_distinct_nrzb(self, parent, index, new_elem):
        for new_child in new_elem:
            parent.insert(index, new_child)
            index += 1

    def convert_distinct_nrzb(self, root):
        for elem in root.iter():
            if elem.tag is etree.PI or elem.tag is etree.Comment or self.is_span_note(elem):
                continue
            new_elem = self.correct_distinct_nrzb(elem.text)
            if new_elem is not None:
                elem.text = new_elem.text
                self.insert_distinct_nrzb(elem, 0, new_elem)
            new_elem = self.correct_distinct_nrzb(elem.tail)
            if new_elem is not None:
                elem.tail = new_elem.text
                parent = elem.getparent()
                self.insert_distinct_nrzb(parent, parent.index(elem), new_elem)
    '''
    @staticmethod
    def convert_old_distinct(text):
        if text is None:
            return text
        p0 = text.find('{')
        if p0 != -1:
            if text.find('}', p0) == -1:
                raise etree.LxmlError("closing '}' not found")
            text = text.replace('  ', ' ').replace(' {', '{')
            x = text.split(" ")
            for i in range(len(x)):
                el = x[i].split("{")
                if len(el) > 1:
                    q = re.search(_charsRe, el[0])
                    if q is not None:
                        begin = el[0][:q.start()]
                        distinct = el[0][q.start():]
                        (form, sep, end) = el[1].partition("}")
                        form = form.replace("*", "")
                        x[i] = u"%s<distinct form=\"%s\">%s</distinct>%s" % (begin, _quoteattr(distinct), form, end)
            # code from speach-cleaner.py end
            text = " ".join(x)
        return text
    '''

    def test_emptytail(self, elem, tail=True):
        text = elem.tail if tail else elem.text
        if text is None or text.isspace() or not tail and len(text) <= 5:
            return
        if len(text) > 10:
            text = text[:10]+'...'
        text = text.replace('\n', '\\n')
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        posname = 'followed by' if tail else 'in'
        self.err_proc("text '" + text + "' outside <speech> " + posname + " <" + elem.tag + ">")

    def test_outbound_text(self, root):
        body = root.find('body')
        if body is None:
            raise etree.LxmlError("<body> tag not found")
        self.line = body.sourceline
        self.test_emptytail(body)
        for check_elem in body:
            if  check_elem.tag == 'speech':
                pass
            elif self.is_span_note(check_elem):
                self.test_emptytail(check_elem)
            elif check_elem.tag == 'p' and 'class' in check_elem.attrib and check_elem.attrib['class'] in ('h1','footnote', 'h2', 'H1', 'H2'):
                self.test_emptytail(check_elem)
            elif check_elem.tag == 'p' and len(check_elem.attrib) == 0:
                for elem in check_elem.iter():
                    if not(self.is_span_note(elem) or self.is_noindex(elem) or elem is check_elem):
                        self.err_proc("wrong tag " + elem.tag + ' in tag <p>')
                    else:
                        self.test_emptytail(elem)
                self.test_emptytail(check_elem, False)
                '''if check_elem.text is not None and len(check_elem.text) > 5:
                    self.err_proc("text outside <speech> in <" + check_elem.tag+'>')'''
            elif self.is_noindex(check_elem):
                self.test_emptytail(check_elem)
            elif check_elem.tag is etree.PI or check_elem.tag is etree.Comment:
                pass
            else:
                listattr = [key + ' = "' + value + '"' for key, value in check_elem.attrib.iteritems()]
                strattr = ' ' + ' '.join(listattr)
                if isinstance(strattr, unicode):
                    strattr = strattr.encode('utf-8')
                self.err_proc("wrong tag " + check_elem.tag + strattr)

        self.line = -1



    @staticmethod
    def is_span_note(elem):
        return elem.tag == 'span' and 'class' in elem.attrib and elem.attrib['class'] == 'note'
    @staticmethod
    def is_noindex(elem):
        if elem.tag != 'noindex':
            return False
        text = elem.text
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        return elem.tag == 'noindex' and text == '[нрзб]'


    def convert_file_lxml(self, tree):
        isKino = 'accent_main/texts/kino' in self.inpname or 'accent_main/texts/theater' in self.inpname \
                 or 'accent_main/texts/reading' in self.inpname
        root = tree.getroot()
        self.lowercase_attrib(root)
        self.convert_p_sp(root)
        self.speach2speech(root)
        self.convert_noindex2span(root)
        self.convert_role2actor(root)
        self.convert_distinct_nrzb(root)
        self.test_outbound_text(root)
        '''
        self.line = body.sourceline
        self.test_emptytail(body)
        for check_elem in body:
            # in spoken documents <body> should contain <speech> tags only
            self.line = check_elem.sourceline
            if check_elem.tag == 'speech':
                if not isKino:
                    # rename 'role' attribute to 'actor'
                    role = check_elem.attrib.get('role', None)
                    if role is not None:
                        if role == '':
                            del check_elem.attrib['role']
                            #self.err_proc('delete enpty role')
                        else:
                            actor = check_elem.attrib.get('actor', None)
                            if actor is not None:
                                if actor == '':
                                    del check_elem.attrib['actor']
                                    #self.err_proc('delete empty actor')
                                else:
                                    self.err_proc("tag speach in non-cinema/theater/reading document has 'role' and 'actor' attribute ")
                                continue
                            check_elem.attrib['actor'] = role
                            del check_elem.attrib['role']
                            if isinstance(role, unicode):
                                role = role.encode('utf-8')
                            #self.err_proc(' rename role = "'+role+'" to actor')
                for elem in check_elem.iter():
                    self.line = elem.sourceline
                    elem.text = self.convert_old_distinct(elem.text)
                    if elem.tag != 'noindex' or elem.text != u'[нрзб]':
                        elem.text = nrzb(elem.text)
                    elem.tail = nrzb(self.convert_old_distinct(elem.tail))
                self.test_emptytail(check_elem)
            elif self.is_span_note(check_elem):
                self.test_emptytail(check_elem)
            elif check_elem.tag == 'p' and 'class' in check_elem.attrib and check_elem.attrib['class'] in ('h1','footnote', 'h2', 'H1', 'H2'):
                self.test_emptytail(check_elem)
            elif check_elem.tag == 'p' and len(check_elem.attrib) == 0:
                for elem in check_elem.iter():
                    if not(self.is_span_note(elem) or self.is_noindex(elem) or elem is check_elem):
                        self.err_proc("wrong tag " + elem.tag + ' in tag <p>')
                    else:
                        self.test_emptytail(elem)
                self.test_emptytail(check_elem, False)
                ''if check_elem.text is not None and len(check_elem.text) > 5:
                    self.err_proc("text outside <speech> in <" + check_elem.tag+'>')''
            elif self.is_noindex(check_elem):
                self.test_emptytail(check_elem)
            elif check_elem.tag is etree.PI or check_elem.tag is etree.Comment:
                pass
            else:
                listattr = [key + ' = "' + value + '"' for key, value in check_elem.attrib.iteritems()]
                strattr = ' ' + ' '.join(listattr)
                if isinstance(strattr, unicode):
                    strattr = strattr.encode('utf-8')
                self.err_proc("wrong tag " + check_elem.tag + strattr)

        self.line = -1
        '''

'''
        for speach in root.iter('speach'):

        for p in root.iter('speech'):
            self.line = p.sourceline
            tmp_tail = p.tail
            p.tail = None
            tmp = etree.tostring(p, encoding='unicode').replace(" \n", " ").replace("\n", " ")
            if tmp.find('{') == -1:
                p.tail = tmp_tail
                continue
            #exclude open and close tags
            pos1 = tmp.find('>')
            pos2 = tmp.rfind('<')
            if pos1+1 == pos2:
                continue
            tmp1, tmp2 = tmp[0:pos1+1], tmp[pos2:]
            tmp = tmp[pos1+1:pos2]
            # code from speach-cleaner.py begin
            x = tmp.split(" ")
            for i in range(len(x)):
                el = x[i].split("{")
                if len(el) > 1:
                    q = re.search(_charsRe, el[0])
                    if q is not None:
                        begin = el[0][:q.start()]
                        distinct = el[0][q.start():]
                        (form, sep, end) = el[1].partition("}")
                        form = form.replace("*", "")
                        x[i] = u"%s<distinct form=\"%s\">%s</distinct>%s" % (begin, _quoteattr(distinct), form, end)
            # code from speach-cleaner.py end
            ppp = tmp1 + nrzb(" ".join(x)) + tmp2
            self.linestr = ppp
            p_n = etree.fromstring(ppp)
            p_n.tail = tmp_tail
            p.getparent().replace(p, p_n)
            self.line = None
            self.linestr = None

'''
