# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from codecs import getwriter
from copy import deepcopy
import hashlib
from inspect import isgenerator
import logging
from os import chmod, makedirs
from os.path import dirname, exists
import stat
from sys import stderr, stdout

from requests import get

__GETATTR_CACHE = {}
__GETATTR_NODEFAULT = "very_unlikely_default_value"


LOG = logging.getLogger('bundlewrap')

MODE644 = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH

try:
    STDERR_WRITER = getwriter('utf-8')(stderr.buffer)
except AttributeError:  # Python 2
    STDERR_WRITER = getwriter('utf-8')(stderr)

try:
    STDOUT_WRITER = getwriter('utf-8')(stdout.buffer)
except AttributeError:  # Python 2
    STDOUT_WRITER = getwriter('utf-8')(stdout)


def cached_property(prop):
    """
    A replacement for the property decorator that will only compute the
    attribute's value on the first call and serve a cached copy from
    then on.
    """
    def cache_wrapper(self):
        if not hasattr(self, "_cache"):
            self._cache = {}
        if prop.__name__ not in self._cache:
            return_value = prop(self)
            if isgenerator(return_value):
                return_value = tuple(return_value)
            self._cache[prop.__name__] = return_value
        return self._cache[prop.__name__]
    return property(cache_wrapper)


def download(url, path):
    if not exists(dirname(path)):
        makedirs(dirname(path))
    if exists(path):
        chmod(path, MODE644)
    with open(path, 'wb') as f:
        r = get(url, stream=True)
        r.raise_for_status()
        for block in r.iter_content(1024):
            if not block:
                break
            else:
                f.write(block)


def get_file_contents(path):
    with open(path, 'rb') as f:
        content = f.read()
    return content


def get_all_attrs_from_file(path, cache=True, base_env=None):
    """
    Reads all 'attributes' (if it were a module) from a source file.
    """
    if base_env is None:
        base_env = {}
    if base_env:
        # do not allow caching when passing in a base env because that
        # breaks repeated calls with different base envs for the same
        # file
        cache = False
    if path not in __GETATTR_CACHE or not cache:
        source = get_file_contents(path)
        env = base_env.copy()
        try:
            exec(source, env)
        except:
            LOG.error("Exception while executing {} "
                      "(use --debug to get a traceback):".format(path))
            raise
        if cache:
            __GETATTR_CACHE[path] = env
    else:
        env = __GETATTR_CACHE[path]
    return env


def getattr_from_file(path, attrname, base_env=None, cache=True, default=__GETATTR_NODEFAULT):
    """
    Reads a specific 'attribute' (if it were a module) from a source
    file.
    """
    env = get_all_attrs_from_file(path, base_env=base_env, cache=cache)
    if default == __GETATTR_NODEFAULT:
        return env[attrname]
    else:
        return env.get(attrname, default)


def graph_for_items(
    title,
    items,
    cluster=True,
    concurrency=True,
    static=True,
    regular=True,
    reverse=True,
    auto=True,
):
    items = sorted(items)

    yield "digraph bundlewrap"
    yield "{"

    # Print subgraphs *below* each other
    yield "rankdir = LR"

    # Global attributes
    yield ("graph [color=\"#303030\"; "
                  "fontname=Helvetica; "
                  "penwidth=2; "
                  "shape=box; "
                  "style=\"rounded,dashed\"]")
    yield ("node [color=\"#303030\"; "
                 "fillcolor=\"#303030\"; "
                 "fontcolor=white; "
                 "fontname=Helvetica; "
                 "shape=box; "
                 "style=\"rounded,filled\"]")
    yield "edge [arrowhead=vee]"

    item_ids = []
    for item in items:
        item_ids.append(item.id)

    if cluster:
        # Define which items belong to which bundle
        bundle_number = 0
        bundles_seen = []
        for item in items:
            if item.bundle is None or item.bundle.name in bundles_seen:
                continue
            yield "subgraph cluster_{}".format(bundle_number)
            bundle_number += 1
            yield "{"
            yield "label = \"{}\"".format(item.bundle.name)
            yield "\"bundle:{}\"".format(item.bundle.name)
            for bitem in item.bundle.items:
                if bitem.id in item_ids:
                    yield "\"{}\"".format(bitem.id)
            yield "}"
            bundles_seen.append(item.bundle.name)

    # Define dependencies between items
    for item in items:
        if static:
            for dep in item.NEEDS_STATIC:
                if dep in item_ids:
                    yield "\"{}\" -> \"{}\" [color=\"#3991CC\",penwidth=2]".format(item.id, dep)

        if regular:
            for dep in item.needs:
                if dep in item_ids:
                    yield "\"{}\" -> \"{}\" [color=\"#C24948\",penwidth=2]".format(item.id, dep)

        if auto:
            for dep in sorted(item._deps):
                if dep in item._concurrency_deps:
                    if concurrency:
                        yield "\"{}\" -> \"{}\" [color=\"#714D99\",penwidth=2]".format(item.id, dep)
                elif dep in item._reverse_deps:
                    if reverse:
                        yield "\"{}\" -> \"{}\" [color=\"#D18C57\",penwidth=2]".format(item.id, dep)
                elif dep not in item.NEEDS_STATIC and dep not in item.needs:
                    if dep in item_ids:
                        yield "\"{}\" -> \"{}\" [color=\"#6BB753\",penwidth=2]".format(item.id, dep)

    # Global graph title
    yield "fontsize = 28"
    yield "label = \"{}\"".format(title)
    yield "labelloc = \"t\""
    yield "}"


def hash_local_file(path):
    """
    Retuns the sha1 hash of a file on the local machine.
    """
    return sha1(get_file_contents(path))


class _Atomic(object):
    """
    This and the following related classes are used to mark objects as
    non-mergeable for the purposes of merge_dict().
    """
    pass


class _AtomicDict(dict, _Atomic):
    pass


class _AtomicList(list, _Atomic):
    pass


class _AtomicSet(set, _Atomic):
    pass


class _AtomicTuple(tuple, _Atomic):
    pass


ATOMIC_TYPES = {
    dict: _AtomicDict,
    list: _AtomicList,
    set: _AtomicSet,
    tuple: _AtomicTuple,
}


def merge_dict(base, update):
    """
    Recursively merges the base dict into the update dict.
    """
    if not isinstance(update, dict):
        return update

    merged = deepcopy(base)

    for key, value in update.items():
        merge = key in base and not isinstance(value, _Atomic)
        if merge and isinstance(base[key], dict):
            merged[key] = merge_dict(base[key], value)
        elif (
            merge and
            isinstance(base[key], list) and
            (
                isinstance(value, list) or
                isinstance(value, set) or
                isinstance(value, tuple)
            )
        ):
            extended = deepcopy(base[key])
            extended.extend(value)
            merged[key] = extended
        elif (
            merge and
            isinstance(base[key], tuple) and
            (
                isinstance(value, list) or
                isinstance(value, set) or
                isinstance(value, tuple)
            )
        ):
            merged[key] = base[key] + tuple(value)
        elif (
            merge and
            isinstance(base[key], set) and
            (
                isinstance(value, list) or
                isinstance(value, set) or
                isinstance(value, tuple)
            )
        ):
            merged[key] = base[key].union(set(value))
        else:
            merged[key] = value

    return merged


def names(obj_list):
    """
    Iterator over the name properties of a given list of objects.

    repo.nodes          will give you node objects
    names(repo.nodes)   will give you node names
    """
    for obj in obj_list:
        yield obj.name


def sha1(data):
    """
    Returns hex SHA1 hash for input.
    """
    hasher = hashlib.sha1()
    hasher.update(data)
    return hasher.hexdigest()
