import re


html_tag_pat = re.compile(r'(<.*?>)+')


def replace_html_tag(s, replace=''):
    return html_tag_pat.sub(replace, s)
