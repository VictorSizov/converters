# -*- Encoding: utf-8 -*-
from lxml import etree

import os
import sys
import time


class ConverterBase:

    def __init__(self, args):
        self.inppath = args.inppath
        self.outpath = args.outpath
        self.files = args.files
        self.outcode = args.outcode
        self.action = args.action if hasattr(args, 'action') else ''
        self.line = -1
        self.inpname = ''
        self.errname = ''
        self.errline = -1
        self.base = u'/place/ruscorpora/corpora_svn/'
        self.wrong_docs = 0

    def err_proc(self, mess):
        if self.errname == self.inpname:
            if self.errline == self.line:
                return
        else:
            self.wrong_docs += 1
        self.errname = self.inpname
        self.errline = self.line
        inpname = self.inpname
        if inpname[:len(self.base)] == self.base:
            inpname = inpname[len(self.base):]
        print >> sys.stderr, 'Error in', inpname, 'line', self.line, ': ', mess

    def convert_file_lxml(self, tree):
        raise Exception('you should rewrite this function in derived class')

    def convert_file(self, inpfile, outfile):
        try:
            self.inpname = inpfile
            tree = etree.parse(inpfile)
            self.convert_file_lxml(tree)
            outdir = os.path.dirname(outfile)
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            with open(outfile, 'w') as fout:
                fout.write('<?xml version="1.0" encoding="{0}"?>\n'.format(self.outcode))
                tree.write(fout, encoding=self.outcode, xml_declaration=False)
            # tree.write(outfile, encoding=self.outcode, xml_declaration=True)
        except etree.LxmlError as e:
            self.wrong_docs += 1
            if self.line != -1:
                print >> sys.stderr, 'Error in', inpfile, 'line', self.line, ':', e.message

    def convert(self):
        d1 = time.clock()
        if self.files == '-':
            self.convert_file(self.inppath, self.outpath)
        else:
            paths = []
            if self.files == '*':
                os.chdir(self.inppath)
                for root, dirs, files in os.walk('.'):
                    if files:
                        root = root[2:]
                        paths += [os.path.join(root, f) for f in files if os.path.splitext(f)[1] in ('.xml', '.xhtml')]
            else:
                with open(self.files) as flist:
                    paths = flist.read().splitlines()
            nn = len(paths)
            i = 0
            for p in paths:
                i += 1
                if i % 250 == 0:
                    print "processed ", i, "total", nn
                self.convert_file(os.path.join(self.inppath, p), os.path.join(self.outpath, p))
        d2 = time.clock()
        print 'processing time', d2-d1, 'sec'
        if self.wrong_docs > 0:
            print >> sys.stderr, "errors found in ", self.wrong_docs, " documents."
            print "errors found in ", self.wrong_docs, " documents. see stderr"


