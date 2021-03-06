# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from os import environ
from os.path import normpath
from random import choice
from string import digits, ascii_letters
from sys import version_info

from . import STDERR_WRITER


VALID_NAME_CHARS = digits + ascii_letters + "-_.+"


def ansi_wrapper(colorizer):
    if environ.get("BWCOLORS", "1") != "0":
        return colorizer
    else:
        return lambda s, **kwargs: s


@ansi_wrapper
def bold(text):
    return "\033[1m{}\033[0m".format(text)


@ansi_wrapper
def green(text):
    return "\033[32m{}\033[0m".format(text)


@ansi_wrapper
def red(text):
    return "\033[31m{}\033[0m".format(text)


@ansi_wrapper
def yellow(text):
    return "\033[33m{}\033[0m".format(text)


def error_summary(errors):
    if not errors:
        return

    if len(errors) == 1:
        STDERR_WRITER.write(_("\n{x} There was an error, repeated below.\n\n").format(
            x=red("!!!"),
        ))
        STDERR_WRITER.flush()
    else:
        STDERR_WRITER.write(_("\n{x} There were {count} errors, repeated below.\n\n").format(
            count=len(errors),
            x=red("!!!"),
        ))
        STDERR_WRITER.flush()

    for e in errors:
        STDERR_WRITER.write(e)
        STDERR_WRITER.write("\n")
        STDERR_WRITER.flush()


def force_text(data):
    """
    Try to return a text aka unicode object from the given data.
    Also has Python 2/3 compatibility baked in. Oh the humanity.
    """
    if version_info < (3, 0):
        if isinstance(data, str):
            return data.decode('utf-8', 'replace')
    else:
        if isinstance(data, bytes):
            return data.decode('utf-8', 'replace')
    return data


def is_subdirectory(parent, child):
    """
    Returns True if the given child is a subdirectory of the parent.
    """
    parent = normpath(parent)
    child = normpath(child)

    if not parent.startswith("/") or not child.startswith("/"):
        raise ValueError(_("directory paths must be absolute"))

    if parent == child:
        return False

    if parent == "/":
        return True

    return child.startswith(parent + "/")


def mark_for_translation(s):
    return s
_ = mark_for_translation


def randstr(length=24):
    """
    Returns a random alphanumeric string of the given length.
    """
    return ''.join(choice(ascii_letters + digits) for c in range(length))


def validate_name(name):
    """
    Checks whether the given string is a valid name for a node, group,
    or bundle.
    """
    try:
        for char in name:
            assert char in VALID_NAME_CHARS
        assert not name.startswith(".")
    except AssertionError:
        return False
    return True


def wrap_question(title, body, question):
    output = ("\n"
              " ╭  {}\n"
              " ┃\n".format(title))
    for line in body.splitlines():
        output += " ┃   {}\n".format(line)
    output += (" ┃\n"
               " ╰  " + question)
    return output
