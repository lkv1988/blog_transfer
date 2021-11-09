Mubu2Markdown
---

## Usage

1. Export your mubu post to HTML format
2. In Python code, construct a MubuPost by your exported html file

```python
    p = MubuPost(output_html_path='<path to your exported html file>', use_mubu_img=True)
```

> `use_mubu_img`: set `True` to show MUBU uploaded image in the output, otherwise `False`

3. Call `to_markdown()` method, then pick your markdown file in the same directory

```python
    p.to_markdown('<maybe some name or default will be the title>')
```

## Custom Token

To make sure your exported markdown will show as you wish, take the following rules:
1. the script will take every line as normal content, it's the basic
2. prefix with `- `(don't forget one blank in it) to make a line as a sub-item
3. prefix with `1. `(one blank too) number and dot to make a line as a sub-item with number
4. prefix with `> `(one blank) to make a line as a note
5. other markdown token will be auto compat:
   1. wrap with single "`" to make a one-line code
   2. wrap with "```" to make multi-line code (now need to be adjusted by manual)
   3. prefix with `#` to make line as a `Hx`(x is the count of `#`) title
   4. `![]()` for image
   5. `[]()` for link
   6. wrap with `**` make text **bold**
   7. wrap with `*` make text *italic*
   8. wrap with `~~` make text ~~strikethrough~~
   9. wrap with `***` make text both **bold** and *italic*
6. and other text will follow your markdown editor's render rule


