"""
http://opml.org/spec2.opml
"""

import pathlib
from lxml import etree
from abc import abstractmethod


class Element:
    @abstractmethod
    def my_tag(self):
        pass

    @abstractmethod
    def is_valid(self):
        pass

    def _on_append_attributes(self, collector: dict):
        pass

    def children_content(self):
        return ''

    def has_children(self):
        return False

    @staticmethod
    def _add_property(s, key, value):
        return f'{s} {key}="{value}"'

    def __str__(self):
        return self.my_tag()

    def to_xml_string(self):
        s = '<' + self.my_tag()
        attrs = {}
        self._on_append_attributes(attrs)
        if attrs and len(attrs) > 0:
            for k, v in attrs.items():
                s = self._add_property(s, k, v)
        if self.has_children():
            s += '>\n'
            s += self.children_content()
            s += f'</{self.my_tag()}>'
        else:
            s += '/>'
        return s


class Head(Element):
    def is_valid(self):
        return self.title is not None

    def __init__(self, title: str, create_date=None, modified_date=None,
                 owner_name=None, owner_email=None):
        assert title
        # don't care other attributes
        self.title = title
        self.create_date = create_date
        self.modified_date = modified_date
        self.owner_name = owner_name
        self.owner_email = owner_email

    def my_tag(self):
        return 'head'

    def __str__(self):
        return super().__str__() + f' title={self.title}'

    def _on_append_attributes(self, attrs):
        if self.title:
            attrs['title'] = self.title
        if self.create_date:
            attrs['dateCreated'] = self.create_date
        if self.modified_date:
            attrs['dateModified'] = self.modified_date
        if self.owner_name:
            attrs['ownerName'] = self.owner_name
        if self.owner_email:
            attrs['ownerEmail'] = self.owner_email


class Outline(Element):
    def is_valid(self):
        return self.text is not None

    def __init__(self, text: str, sub_outlines=None, attrs=None):
        assert text
        self.text = text
        self.sub_outlines = sub_outlines
        self.attrs = attrs

    def append_child(self, child):
        if not self.sub_outlines:
            self.sub_outlines = []
        self.sub_outlines.append(child)

    def __str__(self):
        return super().__str__() + f' text={self.text}, children={0 if not self.sub_outlines else len(self.sub_outlines)}'

    def my_tag(self):
        return 'outline'

    def has_children(self):
        return self.sub_outlines and len(self.sub_outlines) > 0

    def _on_append_attributes(self, collector: dict):
        collector['text'] = self.text
        if not self.attrs or len(self.attrs) == 0:
            return
        for k, v in self.attrs.items():
            collector[k] = v

    def children_content(self):
        s = ''
        for so in self.sub_outlines:
            s += f'{so.to_xml_string()}\n'
        return s


class Body(Element):
    def is_valid(self):
        if len(self.outlines) == 0:
            return False
        for l in self.outlines:
            if not l.is_valid():
                return False
        return True

    def __init__(self, outlines: [Outline]):
        self.outlines = outlines

    def my_tag(self):
        return 'body'

    def has_children(self):
        return True

    def children_content(self):
        if not self.outlines or len(self.outlines) == 0:
            raise RuntimeError("No one outline found.")
        s = ''
        for o in self.outlines:
            s += f'{o.to_xml_string()}\n'
        return s


class OPML(Element):
    def is_valid(self):
        return self.head.is_valid() and self.body.is_valid()

    def my_tag(self):
        return 'opml'

    def __init__(self, head: Element, body: Element):
        assert head
        assert body
        self.head = head
        self.body = body

    def has_children(self):
        return True

    def _on_append_attributes(self, collector: dict):
        collector['version'] = '2.0'

    def children_content(self):
        return f'{self.head.to_xml_string()}\n{self.body.to_xml_string()}'


class Generator:
    def __init__(self, opml: OPML, file_name):
        self.file_name = file_name
        self.opml = opml

    def write(self, path):
        file_path = f'{path}/{self.file_name}.xml'
        if pathlib.Path(file_path).exists():
            raise RuntimeError(f'File already exist: {file_path}')
        with open(file_path, mode='w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(self.opml.to_xml_string())

        print(f'DONE output file: {file_path}')


class Parser:
    def __init__(self, xml_string: str = None, file_path: str = None):
        assert xml_string or file_path
        if xml_string:
            self.xml_bytes = bytes(xml_string, encoding='utf-8')
        else:
            p = pathlib.Path(file_path)
            if not p.exists() or not p.is_file():
                raise RuntimeError(f'IO Error, target file ({file_path}) cant open in the right way, please make sure '
                                   f'it exist and is a file format.')
            with open(file_path, 'r', encoding='utf-8') as source_file:
                self.xml_bytes = bytes(source_file.read(), encoding='utf-8')
        assert len(self.xml_bytes) > 0
        try:
            etree.XML(self.xml_bytes)
        except Exception as e:
            raise RuntimeError('Input content is not a valid XML, please check it.', e)

    @staticmethod
    def _config_parser():
        return etree.XMLParser(
            ns_clean=True,
            remove_comments=True,
            no_network=True,
            load_dtd=False,
            huge_tree=False
        )

    """
      tag  key in attrib attrib[key]
       |       |           |
    <xml_tag attriKey="attrValue">
    """

    def parse(self):
        xml_tree = etree.fromstring(self.xml_bytes, parser=self._config_parser())
        is_opml = False

        head = None
        body = None

        outline_stack = []

        body_outlines = []

        def opt_value(atts: dict, key: str):
            assert atts
            return atts[key] if key in atts else None

        for event, raw_n in etree.iterwalk(xml_tree, events=('start', 'end')):
            # str
            tag = raw_n.tag
            # dict
            attrs = raw_n.attrib
            # line in file
            source_line = raw_n.sourceline
            if event == 'start':
                if tag == 'opml':
                    if is_opml:
                        raise SyntaxError('<opml> already entered, but there has another one at line:' + source_line)
                    else:
                        is_opml = True
                elif tag == 'head':
                    head_title = opt_value(attrs, 'title')
                    if not head_title:
                        raise SyntaxError('<head> must has a "title" attribute, line:' + source_line)
                    create_date = opt_value(attrs, 'dateCreated')
                    modified_date = opt_value(attrs, 'dateModified')
                    owner_name = opt_value(attrs, 'ownerName')
                    owner_email = opt_value(attrs, 'ownerEmail')
                    head = Head(head_title, create_date, modified_date,
                                owner_name, owner_email)
                elif tag == 'outline':
                    text = opt_value(attrs, 'text')
                    if not text:
                        raise SyntaxError('<outline> must has a "title" attribute, line:' + source_line)
                    y = {}
                    for k, y[k] in attrs.items():
                        pass
                    y.pop('text', None)
                    o = Outline(text, None, y if len(y) > 0 else None)
                    if len(outline_stack) > 0:
                        top_o = outline_stack[-1]
                        top_o.append_child(o)
                    outline_stack.append(o)
                    if len(outline_stack) == 1:
                        body_outlines.append(o)
            if event == 'end':
                if tag == 'outline':
                    outline_stack.pop()
                elif tag == 'body':
                    body = Body(body_outlines)
                elif tag == 'opml':
                    ret = OPML(head, body)
                    if not ret.is_valid():
                        raise SyntaxError('Wrong OPML structure, check the input content.')
                    return ret


if __name__ == '__main__':
    # o1_1 = Outline('1.1111111', attrs={"q1": "2"})
    # o1_2 = Outline('1.2222222')
    # o1 = Outline('1', [o1_1, o1_2])
    # o2 = Outline('2')
    # o3 = Outline('3')
    # body = Body([o1, o2, o3])
    # head = Head('Demo OPML', owner_name='Kevin Liu')
    # opml = OPML(head, body)
    # # print(opml.to_string())
    # Generator(opml, 'test').write('.')
    o = Parser(file_path='test.xml').parse()
    print(o)
