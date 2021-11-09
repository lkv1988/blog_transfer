Mubu2Markdown
---

Usage:

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
