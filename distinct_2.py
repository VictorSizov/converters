# -*- Encoding: utf-8 -*-
from converter_basic import ConverterBasic, fill_arg_for_converter
from lxml_ext import LxmlExt


class Final(ConverterBasic):
    '''
    def printdata(self, w):
        return
        print len(w.attrib), len(w)
        print 'w.arrts = ', ','.join([key+':'+value for key, value in w.attrib.iteritems()])
        for ana in w:
            print 'ana.arrts = ', ','.join([key+':'+value for key, value in ana.attrib.iteritems()])
        print 'w.text = ', w[-1].tail '''

    def process_lxml_tree(self, tree):
        for distinct in tree.getroot().iter('distinct'):
            form = distinct.attrib.get("form", None)
            if form is None:
                self.err_proc('distinct tag should have attribure "form"')
                continue
            ln = len(distinct)
            if ln == 0:
                self.err_proc('distinct tag should contain at least one tag')
                continue
            w = distinct[0]
            if ln > 1:
                try:
                    for i in range(ln-1, 0, -1):
                        wi = distinct[i]
                        for ana in wi:
                            w.append(ana)
                        wi.getparent().remove(wi)
                except:
                    continue
            for ana in w:
                ana.tail = None
                attr = ana.attrib
                if "gr" not in attr:
                    self.err_proc('"ana" hasn\'t attribure "gr"')
                    continue

                res = attr["gr"].decode('utf-8')+u',искаж'
                attr["gr"] = res
            w[-1].tail = form
            LxmlExt.disband_node(distinct)
        for elem in tree.getroot().iter():
            tmp = sorted(elem.items())
            elem.attrib.clear()
            elem.attrib.update(tmp)


if __name__ == '__main__':

    parser = fill_arg_for_converter('finalizer')
    parser_args = parser.parse_args()
    final = Final(parser_args)
    final.process()
