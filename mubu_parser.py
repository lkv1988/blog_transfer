"""
http://xpather.com/
"""
import os
import re

from lxml import etree
from pathlib import Path
import datetime

from lib.opml_processor import Outline


class MubuPost:
    DATE_FORMAT = '%Y%m%d'

    def __init__(self, output_html_path, use_mubu_img: bool = False):
        assert output_html_path
        p = Path(output_html_path)
        if not p.exists() or not p.is_file():
            raise RuntimeError('Input file is not exist or not a file, please check it. -22')
        self.use_mubu_img = use_mubu_img
        with open(output_html_path, 'r', encoding='utf-8') as source_file:
            dom_bytes = bytes(source_file.read(), encoding='utf-8')
        self.dom = etree.HTML(dom_bytes)
        created_time = os.stat(output_html_path)[-1]
        if created_time > 0:
            dt = datetime.datetime.fromtimestamp(created_time)
            self.created_time = dt.strftime(self.DATE_FORMAT)
        modified_time = os.stat(output_html_path)[-2]
        if modified_time > 0:
            dt = datetime.datetime.fromtimestamp(modified_time)
            self.modified_time = dt.strftime(self.DATE_FORMAT)

    @staticmethod
    def _get_element_attributes(element):
        # like a dict structure
        return element.attrib

    @staticmethod
    def _get_element_source_line(element):
        return element.sourceline

    @staticmethod
    def _get_element_tag(element):
        return element.tag

    @staticmethod
    def _get_element_text(element):
        return element.text

    def _try_find_created_time_in_title(self, title):
        # maybe get a fixed created time in title text
        r = re.compile(r'(\d{8})')
        found = r.findall(title)
        if found and len(found) == 1:
            return found[0]
        else:
            return self.created_time

    def _elements_to_outlines(self, element_children):
        ret = []
        for e in element_children:
            class_name = self._get_element_attributes(e)['class']
            is_normal_node = 'node' in class_name.split(' ')
            assert is_normal_node
            heading_r = re.compile(r'heading(\d)')
            h_n = heading_r.findall(class_name)
            content_spans = e.xpath('div[@class="content mm-editor"]')[0].xpath('span')
            content = ''
            if len(content_spans) == 1:
                content = content_spans[0].text
            else:
                # may be ` ` code style
                for s in content_spans:
                    attrs = self._get_element_attributes(s)
                    if 'class' in attrs and attrs['class'] == 'codespan':
                        content += f'`{s.text}`'
                    else:
                        content += s.text
            outline_attrs = {}
            # mubu image
            if self.use_mubu_img:
                nullable_image_list_arr = e.xpath('ul[@class="image-list"]')
                nullable_image_list = None
                if nullable_image_list_arr and len(nullable_image_list_arr) > 0:
                    nullable_image_list = nullable_image_list_arr[0]
                if nullable_image_list:
                    img_list_arr = nullable_image_list.xpath('li[@class="image-item"]')
                    if img_list_arr and len(img_list_arr) > 0:
                        img_arr = []
                        for img_li in img_list_arr:
                            img_arr.append(img_li.xpath('img[@src]')[0].attrib['src'])
                        outline_attrs['mubu_imgs'] = img_arr
            nullable_note_content = e.xpath('div[@class="note mm-editor"]')
            if len(nullable_note_content) > 0:
                content += '\n'
                maybe_img_or_code = nullable_note_content[0].xpath('span')[0].text
                # user type image
                # TODO multi user type images
                if maybe_img_or_code == '![](':
                    img_url = maybe_img_or_code + nullable_note_content[0].xpath('a[@href]')[0].attrib['href']
                    outline_attrs['mkd_img'] = img_url
                else:
                    large_code_r = re.compile(r'```(.|\n)*```')
                    maybe_code_hit = large_code_r.match(maybe_img_or_code)
                    if maybe_code_hit:
                        outline_attrs['large_code'] = maybe_img_or_code
            if h_n and len(h_n) == 1:
                content = (int(h_n[0]) * '#') + ' ' + content
            o = Outline(content, attrs=outline_attrs)
            sub_children = e.xpath('div[@class="children"]/ul/li')
            if sub_children and len(sub_children) > 0:
                for sub_o in self._elements_to_outlines(sub_children):
                    o.append_child(sub_o)
            ret.append(o)
        return ret

    def parse(self):
        # <div class="title"> user input text </div>
        title = self._get_element_text(self.dom.xpath('//div[@class="title"]')[0])
        assert title
        self.created_time = self._try_find_created_time_in_title(title)
        source_content = self._get_element_text(self.dom.xpath('//div[@class="publish"]/a')[0])
        if not source_content or str(source_content).strip() != '幕布文档':
            raise SyntaxError('Not MUBU html， please check it. -32')
        node_list_xp = self.dom.xpath('//body/ul[@class="node-list"]')
        if not node_list_xp or len(node_list_xp) != 1:
            raise SyntaxError('Find node-list error, please check the output html. -35')
        root_element = node_list_xp[0]
        root = Outline('Stub')
        for c in self._elements_to_outlines(root_element.xpath('li')):
            root.append_child(c)
        return root


if __name__ == '__main__':
    pass
