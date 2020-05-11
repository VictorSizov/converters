# -*- Encoding: utf-8 -*-
import lxml.etree
import string
import regex


class LxmlExt:

    uni = regex.compile(u'\p{L}+')

    @staticmethod
    def form_uni_str(first, last):
        return u''.join([chr(i) for i in range(ord(first), ord(last)+1)])

    @classmethod
    def is_informative(cls, text):
        if text is None:
            return False
        if isinstance(text, str):
            text = text.decode('utf-8')
        else:
            raise Exception("Wrong type")
        ret = cls.uni.search(text)
        return ret is not None

    @classmethod
    def split_left_spaces(cls, text):
        right = text.lstrip()
        return text[:len(text)-len(right)], right

    @staticmethod
    def concat_text(first, second):
        if first is None:
            first = second
        elif second is not None:
            first += second
        return first

    @staticmethod
    def add_to_sibling(elem, base):
        parent = base.getparent()
        if parent is None:
            raise Exception("root node cannot be sibling")
        parent.insert(parent.index(base)+1, elem)

    @classmethod
    def disband_node(cls, elem):
        parent = elem.getparent()
        if parent is None:
            raise Exception("Cannot disband root node")
        previous = elem.getprevious()
        n_child = len(elem)
        if n_child == 0:
            elem.text = cls.concat_text(elem.text, elem.tail)
        else:
            elem[n_child-1].tail = cls.concat_text(elem[n_child-1].tail, elem.tail)
        index = 0
        if previous is not None:
            index = parent.index(previous)+1
            previous.tail = cls.concat_text(previous.tail, elem.text)
        else:
            parent.text = cls.concat_text(parent.text, elem.text)
        if n_child > 0:
            for child in elem:
                parent.insert(index, child)
                index += 1
        parent.remove(elem)

    @classmethod
    def surround_tail(cls, elem, new_node):
        elem.tail, new_node.text = cls.split_left_spaces(elem.tail)
        cls.add_to_sibling(new_node, elem)
        return new_node

    @classmethod
    def surround_node(cls, node, new_node):
        parent = node.getparent()
        parent.replace(node,new_node)
        new_node.append(node)
        return new_node

    @classmethod
    def move_tail_into(cls, elem):
        if elem.tail is None:
            return
        if len(elem) == 0:
            elem.text = LxmlExt.concat_text(elem.text, elem.tail)
        else:
            elem[-1].tail = LxmlExt.concat_text(elem[-1].tail, elem.tail)
        elem.tail = None

    @classmethod
    def move_element_into(cls, elem, base):
        elem.getparent().remove(elem)
        base.append(elem)


