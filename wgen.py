#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import with_statement, print_function

try:
    from http.server import SimpleHTTPRequestHandler
except ImportError:
    from SimpleHTTPServer import SimpleHTTPRequestHandler
try:
    import http.server as BaseHTTPServer
except ImportError:
    import BaseHTTPServer
import codecs
import errno
import fnmatch
import os
import re
import shutil
import types
import webbrowser

import macros
import config

from unidecode import unidecode

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_SRC_PATH = "./site"
TEMPLATES_PATH = ROOT_SRC_PATH + "/templates"
DEFAULT_TEMPLATE = "%s/%s" % (TEMPLATES_PATH, config.TEMPLATE)
ROOT_DST_PATH = "./www"
MARKDOWN_EXTENSION = config.MARKDOWN_EXTENSION
HOST = "0.0.0.0"
PORT = 8000
ENCODING = "utf-8"
DISQUS_SHORTNAME = config.DISQUS_SHORTNAME
GOOGLE_ANALYTICS_ID = config.GOOGLE_ANALYTICS_ID
RE_MACRO = re.compile(
    r"""
    (?:{{)      # start delimiter
    (.*?)       # macro
    (?:}})      # end delimiter
    """,
    re.VERBOSE)
RE_METADATA = re.compile(
    r"""
    (?:\<!--)   # start delimiter
    (.*?)       # comment
    (?:--\>)    # end delimiter
    """,
    re.VERBOSE | re.MULTILINE | re.DOTALL)
RE_METADATA_KEY_VALUE = re.compile(
    r"""
    ([A-Za-z]+)    # key
    (?:\:)    # split
    (.*)    # value
    """,
    re.VERBOSE)


def slugify(text, delim=u'-'):
    """Generates an ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        result.extend(unidecode(word).split())
    return unicode(delim.join(result))


def chunks(lst, number):
    """
    A generator, split list `lst` into `number` equal size parts.
    usage::
    >>> parts = chunks(range(8),3)
    >>> parts
    <generator object chunks at 0xb73bd964>
    >>> list(parts)
    [[0, 1, 2], [3, 4, 5], [6, 7]]
    """
    lst_len = len(lst)
    for i in xrange(0, lst_len, number):
        yield lst[i: i+number]


def fileopen(filename, mode):
    return codecs.open(filename, mode, ENCODING)


def open_as_text(filename):
    with fileopen(filename, "rb") as f:
        return f.read()


def makedir_if_not_exist(folder):
    if not os.path.exists(folder):
        try:
            os.makedirs(folder)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(folder):
                pass
            else:
                raise


def copy(src, dst):
    makedir_if_not_exist(os.path.dirname(dst))
    shutil.copy2(src, dst)


def text_save_as(text, filename):
    makedir_if_not_exist(os.path.dirname(filename))
    with fileopen(filename, "wb") as f:
        f.write(text)


def walk(folder, pattern="*"):
    for root, dirnames, filenames in os.walk(folder):
        for filename in fnmatch.filter(filenames, pattern):
                if not filename.startswith((".", "_")):
                    yield os.path.join(root, filename)


def walk_site(pattern="*"):
    for filename in walk(ROOT_SRC_PATH, pattern):
        yield filename


def get_page_metadata(text):
    metadata = {}
    for comment in re.findall(RE_METADATA, text):
        for line in comment.strip().splitlines():
            try:
                key, value = re.search(RE_METADATA_KEY_VALUE, line).groups()
            except ValueError:
                continue
            metadata[key.strip()] = value.strip()
    return metadata


def get_macros():
    list_macros = {}
    for k, v in macros.__dict__.items():
        if k in macros.MACROS:
            list_macros[k] = v
    return list_macros


def execute_macro(text, namespace):
    return eval(text, namespace)


def replace_macros(text, namespace=None):
    macros = get_macros()
    if namespace:
        namespace = dict(list(namespace.items()) + list(macros.items()))
    else:
        namespace = macros

    def replace(m):
        match = m.group(1)
        tag = m.group(0)
        try:
            repl = namespace[match]
        except KeyError:
            try:
                repl = execute_macro(match, namespace)
            except NameError:
                repl = tag
        if isinstance(repl, types.FunctionType):
            repl = tag
        return str(repl)

    return re.sub(RE_MACRO, replace, text)


def banner(text, ch='=', length=78):
    spaced_text = ' %s ' % text
    return spaced_text.center(length, ch)


# Scripts
def serve(host=HOST, port=PORT, open_browser=False):
    server_address = (HOST, port)
    SimpleHTTPRequestHandler.protocol_version = "HTTP/1.0"
    os.chdir(ROOT_DST_PATH)
    httpd = BaseHTTPServer.HTTPServer(
        server_address, SimpleHTTPRequestHandler)
    print("Serving HTTP on %s port %d ..." % server_address)
    if open_browser:
        webbrowser.open_new_tab("http://%s:%d" % server_address)
    httpd.serve_forever()


def build(serve_site=True):
    html_template = open_as_text(DEFAULT_TEMPLATE)
    gendate = macros.__gendatetime()
    try:
        shutil.rmtree(ROOT_DST_PATH)
    except WindowsError:
        os.makedirs(ROOT_DST_PATH)
    for path_src in walk_site():
        path_dst = path_src.replace("site", "www")
        if not path_src.endswith(MARKDOWN_EXTENSION):
            copy(path_src, path_dst)
        else:
            if os.path.split(path_src) == TEMPLATES_PATH:
                continue
            md_text = open_as_text(path_src)
            html_path_dst = path_dst.replace(MARKDOWN_EXTENSION, ".html")
            path_dst, filename_dst = os.path.split(html_path_dst)
            filename_dst, ext_dst = os.path.splitext(filename_dst)
            html_path_dst = os.path.join(
                path_dst, slugify(filename_dst)) + ext_dst
            url = html_path_dst.replace(ROOT_DST_PATH, "").replace("\\", "/")

            def list_page(**kwargs):
                try:
                    root, md_filename = os.path.split(path_src)
                    pagename = md_filename.replace(MARKDOWN_EXTENSION, "")
                    md_filename = md_filename.replace(pagename, kwargs["path"])
                    if root != ".":
                        path = os.path.join(root, md_filename)
                    del kwargs["path"]
                except KeyError:
                    path = path_src
                return macros.__list_page(path, **kwargs)

            namespace_page = dict(
                list(get_page_metadata(md_text).items()) + [
                    ("url", url), ("list_page", list_page)])
            disqus = macros.__disqus(url=url, title=namespace_page["title"])
            namespace_page["disqus"] = disqus
            if namespace_page.get("date"):
                date_string = macros.date_to_string(namespace_page["date"])
                date_long_string = macros.date_to_long_string(
                    namespace_page["date"])
                namespace_page["date_string"] = date_string
                namespace_page["date_long_string"] = date_long_string
            html_content = macros.markdown_to_html(
                replace_macros(md_text, namespace_page))
            namespace_template = {
                "content": html_content,
                "generated_date": gendate}
            raw_html = replace_macros(html_template, namespace_template)
            text_save_as(raw_html, html_path_dst)
    if serve_site:
        serve()


def help():
    pass


def version():
    pass


def main():
    print(banner("wgen - static site generator"))
    build()


if __name__ == '__main__':
    main()
    # print(slugify("C://test/test/anime. Site.md"))
