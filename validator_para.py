# -*- coding: utf-8 -*-

from validator_basic import ValidatorBasic, add_arguments


class CheckPara(ValidatorBasic):

    def __init__(self, args):
        super().__init__(args)
        self.langs = {
            "arm-rus": "hy_hy2_ru",  "esp-rus": "es_ru",  "pol-rus": "pl_ru",
            "rus-eng": "ru_en",  "rus-latv": "ru_lv",  "ukr-rus": "uk_ru",
            "bash-rus": "ba_ru",   "est-rus": "et_ru",   "rus-arm": "ru_hy_hy2",
            "rus-esp": "ru_es",  "rus-lit": "ru_lt",   "zho-rus": "zh_zh2_ru",
            "bel-rus": "be_ru", "fin-rus": "fi_ru", "rus-bash": "ru_ba", "rus-est": "ru_et", "rus-pol": "ru_pl",
            "bua-rus": "bua_ru", "fra-rus": "fr_ru", "rus-bel": "ru_be", "rus-fin": "ru_fi", "rus-sve": "ru_sv",
            "bul-rus": "bg_ru", "ger-rus": "de_ru", "lit-rus": "lt_ru", "rus-bua": "ru_bua", "rus-fra": "ru_fr",
            "rus-ukr": "ru_uk", "cze-rus": "cs_ru", "ita-rus": "it_ru", "rus-bul": "ru_bg", "rus-ger": "ru_de",
            "rus-zho": "ru_zh_zh2", "eng-rus": "en_ru", "latv-rus": "lv_ru", "rus-cze": "ru_cs",
            "rus-ita": "ru_it", "sve-rus": "sv_ru"}

    def check_first(self, langs_int, lang_path):
        correct = True
        # проверка языков
        var_cmp = langs_int[0][1]
        if var_cmp not in (0, -1):
            correct = False
        else:
            for pair in langs_int[1:]:
                if var_cmp != -1:
                    var_cmp += 1
                if var_cmp != pair[1]:
                    correct = False
                    break
        if correct:
            l_cmp = ''
            l_str = langs_int[0][0]
            for pair in langs_int[1:]:
                if not l_cmp or l_cmp != pair[0] or var_cmp == -1:
                    l_str += '_' + pair[0]
                l_cmp = pair[0]
            if l_str != self.langs[lang_path]:
                correct = False
        return correct

    def process_lxml_tree(self, tree):
        root = tree.getroot()
        base = root.base
        lang_path = base[base.find("/para/texts/")+len("/para/texts/"):].split('/')[0]
        langs = None
        for para in root.iter('para'):
            self.set_line_info(para)
            langs_int = []
            for sent in para.iter('se'):
                langs_int.append((sent.get("lang"), int(sent.get("variant_id", "-1"))))
            langs_curr = ''
            for pair in langs_int:
                if langs_curr:
                    langs_curr += '_'
                langs_curr += pair[0]
                if pair[1] != -1:
                    langs_curr += "({0})".format(pair[1])
            if langs is None:
                correct = self.check_first(langs_int, lang_path)
                if not correct:
                    self.err_proc("{0} Ошибка последовательности языков/вариантов".format(langs_curr))
                else:
                    langs = langs_curr
            elif langs != langs_curr:
                self.err_proc("{0} Ошибка последовательности языков/вариантов".format(langs_curr))
        return None


if __name__ == '__main__':
    parser = add_arguments('para validator')
    parser_args = parser.parse_args()
    check_para = CheckPara(parser_args)
    check_para.process()
