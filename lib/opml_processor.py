"""
http://opml.org/spec2.opml
"""

import pathlib
from abc import abstractmethod


class Element:
    @abstractmethod
    def my_tag(self):
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

    def to_string(self):
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
    def __init__(self, text: str, sub_outlines=None, attrs=None):
        assert text
        self.text = text
        self.sub_outlines = sub_outlines
        self.attrs = attrs

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
            s += f'{so.to_string()}\n'
        return s


class Body(Element):
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
            s += f'{o.to_string()}\n'
        return s


class OPML(Element):
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
        return f'{self.head.to_string()}\n{self.body.to_string()}'


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
            f.write(opml.to_string())

        print(f'DONE output file: {file_path}')


class Parser:
    pass


if __name__ == '__main__':
    o1_1 = Outline('1.1111111', attrs={"q1": "2"})
    o1_2 = Outline('1.2222222')
    o1 = Outline('1', [o1_1, o1_2])
    o2 = Outline('2')
    o3 = Outline('3')
    body = Body([o1, o2, o3])
    head = Head('Demo OPML', owner_name='Kevin Liu')
    opml = OPML(head, body)
    # print(opml.to_string())
    Generator(opml, 'test').write('.')
