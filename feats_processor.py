# -*- coding: utf-8 -*-
from lxml import etree
from processor_basic import ProcessorBasic, fill_arg_for_processor
from pathlib import Path
from collections import Counter
import string

from lxml_ext import LxmlExt

class FeatsErr(Exception):
    def __init__(self, mess):
        super().__init__(mess)
    pass

class FeatsLoader:
    def __init__(self, featsname):
        tree = etree.parse(featsname)
        self.feat=dict()
        gram = tree.getroot().find('gr')
        if gram is not None:
            self.feat['gr'] = {value.text for value in gram.findall('value')}
        self.wrong = set()
    def cmp_feat(self, ana):
        gr = ana.get('gr', None)
        gr_cmp = self.feat.get('gr', None)
        if gr and gr_cmp:
            diff = set(gr.split(',')).difference(gr_cmp)
            if diff:
                if '' in diff:
                    print("Empty!")

                self.wrong.update(diff)
                raise FeatsErr("Wrong feats: " + ','.join(diff))

class FeatsChecker(ProcessorBasic):
    def __init__(self, args):
        super().__init__(args)
        self.feats_loader = FeatsLoader('/home/victor/programs/converters/feats_n.xml')
        self.feats = set()
        self.feat_grs = set()
        self.repl = {
            '家[': '家[jiā]',
            '把[': '把[bǎ]',
            '本[': '本[běn]',
            '条[': '条[tiáo]',
            '片[': '片[piàn]',
            '间': '间[jiān]',
            '间[': '间[jiān]',
            '项[': '项[xiàng]'
        }
        self.punct=Counter()
        self.whites = {u' ',u'\u3000'}

    '''
    Проверка допустимых морф. признаков
    def process_lxml_tree(self, tree):
        root = tree.getroot()
        for se in root.iter('se'):
            if se.get('lang') != 'ru':
                continue
            for ana in se.iter('ana'):
                self.set_line_info(ana)
                try:
                    self.feats_loader.cmp_feat(ana)
                except FeatsErr as ex:
                    self.err_proc(str(ex))
        return tree
    стирание в китайском корпусе русской морфологии, удаление в китайской морфологии характеристики defaulf
   
    def process_lxml_tree(self, tree):
        root = tree.getroot()
        for se in root.iter('se'):
            if se.get('lang') != 'ru':
                continue
            text = ''
            for w in list(se):
                text = LxmlExt.concat_text(text, w.text)
                for ana in list(w):
                    text = LxmlExt.concat_text(text, ana.text)
                    text = LxmlExt.concat_text(text, ana.tail)
                    w.remove(ana)
                text = LxmlExt.concat_text(text, w.tail)
                se.remove(w)
            se.text = text
        return tree
    подсчет документов без существительных
    def process_lxml_tree(self, tree):
        root = tree.getroot()
        num_s = 0
        for ana in root.iter('ana'):
            st = ana.get('gr', "").split(',')
            if 'S' in st:
                num_s += 1
        if num_s == 0:
            self.err_proc("S not found")
    def process_lxml_tree(self, tree):
        root = tree.getroot()
        for se in root.iter('se'):
            if se.get('lang') != 'ru':
                for ana in se.iter('ana'):
                    gr = ana.get('gr', 'DEFAULT')
                    feats = gr.split(',')
                    self.feats.update(feats)
                    self.feat_grs.add(','.join(sorted(feats)))
    def process_lxml_tree(self, tree):
        root = tree.getroot()
        for se in root.iter('se'):
            if se.get('lang') != 'ru':
                for ana in se.iter('ana'):
                    gr = ana.get('gr', 'DEFAULT').replace('，', ',').replace(' ', '')
                    ana.set('gr', gr)
                    sem = ana.get('sem', None)
                    if sem:
                        ana.set('sem', sem.replace('_', chr(160)).replace(' ', ', '))
        return tree
   

    def process_lxml_tree(self, tree):
        root = tree.getroot()
        for se in root.iter('se'):
            if se.get('lang') != 'ru':
                for ana in se.iter('ana'):
                    feats = ana.get('gr', 'DEFAULT').split(',')
                    feats = [self.repl.get(feat, feat) for feat in feats]
                    ana.set('gr', ','.join(feats))
        return tree
    

    def process_lxml_tree(self, tree):
        root = tree.getroot()
        for se in root.iter('se'):
            if se.get('lang') != 'ru':
                for ana in se.iter('ana'):
                    transl = ana.attrib.pop('sem', None)
                    if transl:
                        if ana.get('sem', None):
                            raise Exception("logic error")
                        tr=transl.replace(' ', '').split(',')
                        ana.set('transl', transl)
                    else:
                        transl=transl
                    feats = ana.get('gr', 'DEFAULT').split(',')
                    feats = ['CL:'+feat if ord(feat[0]) > 255 else feat for feat in feats]
                    ana.set('gr', ','.join(feats))
                    tmp = sorted(ana.items())
                    ana.attrib.clear()
                    ana.attrib.update(tmp)

        return tree
   
    def process_lxml_tree(self, tree):
        root = tree.getroot()
        for se in root.iter('se'):
            self.set_line_info(se)
            lang = se.get('lang', '')
            if lang == 'zh_2':
                se.set('lang','zh2')
            elif lang not in ('ru', 'zh', 'zh2'):
                self.err_proc("Wrong language " + lang)
        return tree
    '''
    def process_lxml_tree(self, tree):
        root = tree.getroot()
        for se in root.iter('se'):
            self.set_line_info(se)
            lang = se.get('lang', '')
            '''
            if lang == 'zh' or lang == 'zh2':
                for w in se.iter('w'):
                    if w is not se[-1]:
                        if lang == 'zh' and w.tail and w.tail and w.tail == '\n':
                            w.tail = None
                        if lang == 'zh2' and not w.tail:
                            w.tail = ' '
                repl = (u'\u3000', u' ') if lang == 'zh2' else (u' ', u'\u3000')
                texts = se.xpath(".//text()")
                for txt in texts:
                    if txt.find(repl[0]) != -1:
                        parent = txt.getparent()
                        text_n = txt.replace(repl[0], repl[1])
                        if txt.is_text:
                            parent.text = text_n
                        elif txt.is_tail:
                            parent.tail = text_n
                        else:
                            raise Exception("")
            '''
            if lang == 'zh':
                texts = se.xpath(".//text()")
                for txt in texts:
                    if not LxmlExt.is_informative(txt):
                        self.punct[txt] += 1

        return tree

    def put_info(self):
        '''
        if self.feats_loader.wrong:
            if '' in self.feats_loader.wrong:
                print("Empty!")
            print("Wrong feats: {0}".format(','.join(sorted(self.feats_loader.wrong))))

        with open(Path('~/Documents/china_gr.txt').expanduser(), 'w') as fout:
            fout.write("china feats:\n\n")
            fout.write('\n'.join(sorted(self.feats))+'\n')
            fout.write("china feat sets:\n\n")
            fout.write('\n'.join(sorted(self.feat_grs))+'\n')
        '''
        with open(Path('~/Documents/china_punct.txt').expanduser(), 'w') as fout:
            fout.write("china punct:\n\n")
            for nn in self.punct.most_common(100):
                fout.write('"{0}" - {1}\n'.format(nn[0], nn[1]))


if __name__ == '__main__':
    parser = fill_arg_for_processor('feat checker')
    parser_args = parser.parse_args()
    feats_checker = FeatsChecker(parser_args)
    feats_checker.process()
    feats_checker.put_info()







