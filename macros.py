#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import datetime
import re
import string
import subprocess

import config
from wgen import (
    replace_macros, get_page_metadata, open_as_text, walk, ROOT_SRC_PATH,
    HOST, PORT, DISQUS_SHORTNAME, GOOGLE_ANALYTICS_ID, ROOT_URL, slugify)


# Funtion Macro
def menu():
    menu = '<li><a href="/index.html"></span> home</a></li>\n'
    for filewww in os.listdir(ROOT_SRC_PATH):
        if filewww.endswith(config.MARKDOWN_EXTENSION):
            path = os.path.basename(filewww).replace(
                config.MARKDOWN_EXTENSION, ".html")
            if path != "index.html":
                name = os.path.splitext(path)[0]
                menu += '<li><a href="/%s"> %s</a></li>\n' % (path, name)
    return menu


def markdown_to_html(text):
    pipe = subprocess.Popen(
        "smu",
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True)
    html = pipe.communicate(input=text.encode("utf8"))[0].decode("utf8")
    return html


def __gendatetime(format="%a %b %d %H:%M %Z %Y"):
    return datetime.datetime.today().strftime(format)


def date_format(date, format):
    try:
        date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M")
    except ValueError:
        date = datetime.datetime.strptime(date, "%Y-%m-%d")
    return date.strftime(format)


def date_to_string(date):
    return date_format(date, "%d %b %Y at %H:%M").replace(" at 00:00", "")


def date_to_long_string(date):
    return date_format(date, "%d %B %Y at %H:%M").replace(" at 00:00", "")


def latex_math(latex):
    return "https://chart.googleapis.com/chart?cht=tx&chl=" + latex


def gist(id, filename=None, embed=True):
    if filename:
        embedgist = (
            '<script src="https://gist.github.com/%d.js?file=%s"></script>' % (
                id, filename))
    else:
        embedgist = (
            '<script src="https://gist.github.com/%d.js"></script>' % id)
    return embedgist


def youtube(id, width=560, height=315, related=True, ssl=False, cookie=True):
    """Embed Youtube Video in a page or post"""
    related = "" if related else "?rel=0"
    protocol = "https://" if ssl else "http://"
    if cookie:
        embed_youtube_url = protocol + "www.youtube.com/embed/"
    else:
        embed_youtube_url = protocol + "www.youtube-nocookie.com/embed/"
    options = 'width="%d" height="%d" src="%s%s%s"' % (
        width, height, embed_youtube_url, id, related)
    return '<iframe %s frameborder="0" allowfullscreen></iframe>' % options


def vimeo(id, width=560, height=315, autoplay=False,
          avatar=False, title=True, author=False, color=None):
    if color:
        color = "color=%s" % color.replace("#", "")
    else:
        color = ""
    if not avatar:
        avatar = "portrait=0&"
    else:
        avatar = ""
    if not title:
        title = "title=0&"
    else:
        title = ""
    if not author:
        author = "byline=0"
    else:
        author = ""
    if autoplay:
        autoplay = "?autoplay=1"
    else:
        autoplay = "?"
    url = "http://player.vimeo.com/video/%d%s%s%s%s%s" % (
        id, autoplay, avatar, title, author, color)
    options = 'width="%d" height="%d" src="%s"' % (width, height, url)
    return '<iframe %s frameborder="0" allowfullscreen></iframe>' % options


try:
    rot_13_trans = string.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm")
except AttributeError:
    rot_13_trans = str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm")


def rot_13_encrypt(line):
    """Rotate 13 encryption."""
    line = line.translate(rot_13_trans)
    line = re.sub('(?=[\\"])', r'\\', line)
    line = re.sub('\n', r'\n', line)
    line = re.sub('@', r'\\100', line)
    line = re.sub('\.', r'\\056', line)
    line = re.sub('/', r'\\057', line)
    return line


def js_obfuscated_text(text):
    """
    ROT 13 encryption with embedded in Javascript code to decrypt
    in the browser.
    """
    return """<noscript>(%s)</noscript>
              <script type="text/javascript">
              document.write(
              "%s".replace(/[a-zA-Z]/g,
              function(c){
                return String.fromCharCode(
                (c<="Z"?90:122)>=(c=c.charCodeAt(0)+13)?c:c-26);}));
            </script>""" % (
        "Javascript must be enabled to see this e-mail address",
        rot_13_encrypt(text))


def js_obfuscated_mailto(email, displayname=None):
    """
    ROT 13 encryption within an Anchor tag w/ a mailto: attribute
    """
    if not displayname:
        displayname = email
    return js_obfuscated_text('<a href="mailto:%s">%s</a>' % (
        email, displayname))


def __reading_time(text):
    words_per_minute = 180
    words = len(text.split())
    minutes = int(round(words / words_per_minute, 0))
    minutes_label = "minute" if minutes == 1 else "minutes"
    if minutes > 0:
        return "about %d %s" % (minutes, minutes_label)
    else:
        "less than 1 minute"


def __get_pages(path_src, reverse):
    pages = []
    root, md_filename = os.path.split(path_src)
    pagename = md_filename.replace(config.MARKDOWN_EXTENSION, "")
    root_page = os.path.join(root, pagename)
    if root == ROOT_SRC_PATH:
        if os.path.isdir(root_page):
            for md_filename_src in walk(root_page, "*.md"):
                md_text_page = open_as_text(md_filename_src)

                path_md, filename_md = os.path.split(md_filename_src)
                filename_md, ext_md = os.path.splitext(filename_md)
                md_filename_src = os.path.join(
                    path_md, slugify(filename_md)) + ext_md

                url_page = md_filename_src.replace(
                    ROOT_SRC_PATH, "").replace(
                    config.MARKDOWN_EXTENSION, ".html").replace(
                    "\\", "/")
                namespace_page = dict(
                    list(
                        get_page_metadata(md_text_page).items()) + [
                        ("url", url_page)])
                disqus = __disqus(
                    shortname="", url=url_page, title=namespace_page["title"])
                namespace_page["disqus"] = disqus
                if namespace_page.get("date"):
                    date_string = date_to_string(namespace_page["date"])
                    date_long_string = date_to_long_string(
                        namespace_page["date"])
                    namespace_page["date_string"] = date_string
                    namespace_page["date_long_string"] = date_long_string
                html_content = markdown_to_html(
                    replace_macros(md_text_page, namespace_page))
                page_content = {
                    "namespace": namespace_page,
                    "html": html_content,
                    "url": url_page}
                pages.append(page_content)
    return sorted(pages,
                  key=lambda k: k['namespace']['date'],
                  reverse=reverse)


def __list_page(path, max=None, content=False, reverse=True):
    list_page = ""
    for i, page in enumerate(__get_pages(path, reverse)):
        if i == max:
            break
        if content:
            list_page += "<article>\n%s\n</article>\n\n" % page["html"]
        else:
            title = '<a href="%s">%s</a> - ' % (
                page["url"], page["namespace"]["title"])
            date = "<strong>%s</strong> - " % (
                date_to_long_string(page["namespace"]["date"]))
            abstract = page["namespace"]["abstract"]
            comments_count = '<a href="%s#disqus_thread">Comments</a>' % (
                page["url"])
            list_page += "%s%s%s %s   \n" % (
                title, date, abstract, comments_count)
    return list_page


def google_analytics(id=GOOGLE_ANALYTICS_ID):
    return """<script type="text/javascript">
      var _gaq = _gaq || [];
      _gaq.push(['_setAccount', '%s']);
      _gaq.push(['_trackPageview']);

      (function() {
        var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
        ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
        var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
      })();
    </script>""" % id


def __disqus(shortname=DISQUS_SHORTNAME, url="", host=ROOT_URL, title=""):
    if not host:
        host = HOST.replace("0.0.0.0", "127.0.0.1")
        url = "http://" + host + ":" + str(PORT) + url
    else:
        url = host + url
    return """<div id="disqus_thread"></div>
    <script type="text/javascript">
        /* * * CONFIGURATION VARIABLES: EDIT BEFORE PASTING INTO YOUR WEBPAGE * * */
        var disqus_shortname = '%s'; // required: replace example with your forum shortname
        var disqus_identifier = '%s';
        var disqus_url = '%s';
        var disqus_title = '%s';

        /* * * DON'T EDIT BELOW THIS LINE * * */
        (function() {
            var dsq = document.createElement('script'); dsq.type = 'text/javascript'; dsq.async = true;
            dsq.src = '//' + disqus_shortname + '.disqus.com/embed.js';
            (document.getElementsByTagName('head')[0] || document.getElementsByTagName('body')[0]).appendChild(dsq);
        })();
    </script>
    <noscript>Please enable JavaScript to view the <a href="http://disqus.com/?ref_noscript">comments powered by Disqus.</a></noscript>""" % (
        shortname, url, url, title)


def disqus_comment_count():
    return """<script type="text/javascript">
      /* * * CONFIGURATION VARIABLES: EDIT BEFORE PASTING INTO YOUR WEBPAGE * * */
      var disqus_shortname = '%s'; // required: replace example with your forum shortname
      /* * * DON'T EDIT BELOW THIS LINE * * */
      (function () {
        var s = document.createElement('script'); s.async = true;
        s.type = 'text/javascript';
        s.src = 'http://' + disqus_shortname + '.disqus.com/count.js';
        (document.getElementsByTagName('HEAD')[0] || document.getElementsByTagName('BODY')[0]).appendChild(s);
      }());
    </script>
    <noscript>Please enable JavaScript to view the <a href="http://disqus.com/?ref_noscript">comments powered by Disqus.</a></noscript>""" % (
        DISQUS_SHORTNAME)


# String Macro
blog_title = config.BLOG_TITLE
blog_subtitle = config.BLOG_SUBTITLE
style = config.STYLE
menu = menu()
syntax_color = config.SYNTAX_COLOR
root_url = config.ROOT_URL

# Macros
email = js_obfuscated_mailto
MACROS = [
    "blog_title", "blog_subtitle", "menu", "syntax_color", "style",
    "gist", "latex_math", "date_format", "date_to_string",
    "date_to_long_string", "youtube", "vimeo", "email", "google_analytics",
    "disqus", "disqus_comment_count"]
