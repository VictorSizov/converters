# -*- Encoding: utf-8 -*-

from converter_base import ConverterBase
from converter_common import ConverterCommon
from converter_speach import ConverterSpeach
from test import Test
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Starts converter.')
    parser.add_argument('inppath')
    parser.add_argument('outpath')
    parser.add_argument('files')
    parser.add_argument('outcode', choices=['utf-8', 'windows-1251'], default='utf-8')
    parser.add_argument('--action', choices=['sortattr', 'format', 'conv_sp', 'test', 'clearln', 'old_norm'], default='sortattr')

    args = parser.parse_args()
    if args.action == 'test':
        converter = Test(args)
    elif args.action == 'format' or args.action == 'sortattr' or args.action == 'clearln':
        converter = ConverterCommon(args)
    elif args.action == 'old_norm':
        converter = ConverterCommon(args)
    elif args.action == 'conv_sp':
        converter = ConverterSpeach(args)
    else:
        raise Exception('Unsupported "action" value')
    converter.convert()

