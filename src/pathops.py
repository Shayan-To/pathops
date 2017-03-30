#!/usr/bin/env python
"""
pathops.py - Inkscape extension to apply multiple path operations

This extension takes a selection of path and a group of paths, or several
paths, and applies a path operation with the top-most path in the z-order, and
each selected path or each child of a selected group underneath.

Copyright (C) 2014  Ryan Lerch (multiple difference)
              2016  Maren Hachmann <marenhachmannATyahoo.com>
                    (refactoring, extend to multibool)
              2017  su_v <suv-sf@users.sf.net>
                    Rewrite to support applying to larger selection (max_count)
                    and to improve performance (support one level of grouping,
                    use zSort from pathmodifier instead of external query),
                    extend GUI options (dry-run).

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
# pylint: disable=too-many-ancestors

# standard library
import os
from shutil import copy2
from subprocess import Popen, PIPE

# local library
# local library
try:
    import inkex_local as inkex
except ImportError:
    import inkex
from pathmodifier import zSort as z_sort


__version__ = '0.0'


# Global "constants"
SVG_SHAPES = ('rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon')


# ----- SVG element helper functions

def is_group(node):
    """Check node for group tag."""
    return node.tag == inkex.addNS('g', 'svg')


def is_path(node):
    """Check node for path tag."""
    return node.tag == inkex.addNS('path', 'svg')


def is_basic_shape(node):
    """Check node for SVG basic shape tag."""
    return node.tag in (inkex.addNS(tag, 'svg') for tag in SVG_SHAPES)


def is_custom_shape(node):
    """Check node for Inkscape custom shape type."""
    return inkex.addNS('type', 'sodipodi') in node.attrib


def is_shape(node):
    """Check node for SVG basic shape tag or Inkscape custom shape type."""
    return is_basic_shape(node) or is_custom_shape(node)


def has_path_effect(node):
    """Check node for Inkscape path-effect attribute."""
    return inkex.addNS('path-effect', 'inkscape') in node.attrib


def is_modifiable_path(node):
    """Check node for editable path data."""
    return is_path(node) and not (has_path_effect(node) or
                                  is_custom_shape(node))


def is_image(node):
    """Check node for image tag."""
    return node.tag == inkex.addNS('image', 'svg')


def is_text(node):
    """Check node for text tag."""
    return node.tag == inkex.addNS('text', 'svg')


def does_pathops(node):
    """Check whether node is supported by Inkscape path operations."""
    return (is_path(node) or
            is_shape(node) or
            is_text(node))


# ----- list processing helper functions

def recurse_selection(node, id_list):
    """Recursively process selection, add checked elements to id list."""
    if is_group(node):
        for child in node:
            id_list = recurse_selection(child, id_list)
    elif does_pathops(node):
        id_list.append(node.get('id'))
    return id_list


def simple_selection(node, id_list):
    """Check selection including one group level."""
    if is_group(node):
        for child in node:
            if does_pathops(child):
                id_list.append(child.get('id'))
    elif does_pathops(node):
        id_list.append(node.get('id'))
    return id_list


def chunks(alist, max_len):
    """Chunk a list into sublists of max_len length."""
    for i in range(0, len(alist), max_len):
        yield alist[i:i+max_len]


# ----- process external command, files

def run(cmd_format, stdin_str=None, verbose=False):
    """Run command"""
    if verbose:
        inkex.debug(cmd_format)
    out = err = None
    myproc = Popen(cmd_format, shell=False,
                   stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, err = myproc.communicate(stdin_str)
    if myproc.returncode == 0:
        return out
    elif err is not None:
        inkex.errormsg(err)


def cleanup(tempfile):
    """Clean up tempfile."""
    try:
        os.remove(tempfile)
    except Exception:  # pylint: disable=broad-except
        pass


# ----- PathOps() class, methods

class PathOps(inkex.Effect):
    """Effect-based class to apply Inkscape path operations."""

    def __init__(self):
        """Init base class."""
        inkex.Effect.__init__(self)

        # options
        self.OptionParser.add_option("--ink_verb",
                                     action="store", type="string",
                                     dest="ink_verb", default="difference",
                                     help="Inkscape verb for path op")
        self.OptionParser.add_option("--max_count",
                                     action="store", type="int",
                                     dest="max_count", default=500,
                                     help="Max ops per external run")
        self.OptionParser.add_option("--recursive_sel",
                                     action="store", type="inkbool",
                                     dest="recursive_sel", default=True,
                                     help="Recurse beyond one group level")
        self.OptionParser.add_option("--dry_run",
                                     action="store", type="inkbool",
                                     dest="dry_run", default=False,
                                     help="Dry-run without exec")

    def get_selected_ids(self):
        """Return a list of ids, sorted in z-order."""
        id_list = []
        recursive_sel = True
        if len(self.selected) < 2:
            inkex.errormsg("This extension requires 2 or more selected items.")
            return None
        else:
            if self.options.recursive_sel:
                # unlimited nested levels of groups
                for node in self.selected.values():
                    recurse_selection(node, id_list)
            else:
                # support one group level only
                for node in self.selected.values():
                    simple_selection(node, id_list)
        if len(id_list) < 2:
            inkex.errormsg("This extensions requires paths and shapes.")
            return None
        else:
            return id_list

    def get_sorted_ids(self):
        """Return top-most path, and a list with z-sorted ids."""
        top_path = None
        sorted_ids = None
        id_list = self.get_selected_ids()
        if id_list is not None:
            sorted_ids = z_sort(self.document.getroot(), id_list)
            top_path = sorted_ids.pop()
        return (top_path, sorted_ids)

    def effect(self):
        """Main entry point to process current document."""

        # create a list of ids to process
        top_path, other_paths = self.get_sorted_ids()

        # return early if selection is not supported
        if top_path is None or other_paths is None:
            return

        # options
        max_count = self.options.max_count or 500
        ink_verb = self.options.ink_verb or "SelectionDiff"

        # create a copy of current file in $TEMPDIR
        tempfile = os.path.splitext(self.svg_file)[0] + "-pathops.svg"
        if not self.options.dry_run:
            copy2(self.svg_file, tempfile)

        # loop through sorted id list, process in chunks
        for chunk in chunks(other_paths, max_count):

            # build list with command line arguments
            cmdlist = []
            cmdlist.append("inkscape")
            for child in chunk:
                cmdlist.append("--select=" + top_path)
                cmdlist.append("--verb=EditDuplicate")
                cmdlist.append("--select=" + child)
                cmdlist.append("--verb=" + ink_verb)
                cmdlist.append("--verb=EditDeselect")
            cmdlist.append("--verb=FileSave")
            cmdlist.append("--verb=FileQuit")
            cmdlist.append("-f")
            cmdlist.append(tempfile)

            # process command list
            if self.options.dry_run:
                inkex.debug(cmdlist)
            else:
                run(cmdlist)

        # finish up
        if not self.options.dry_run:
            # replace current document with content of temp copy
            xmlparser = inkex.etree.XMLParser(huge_tree=True)
            self.document = inkex.etree.parse(tempfile, parser=xmlparser)
            # clean up
            cleanup(tempfile)


if __name__ == '__main__':
    ME = PathOps()
    ME.affect()

# vim: et shiftwidth=4 tabstop=8 softtabstop=4 fileencoding=utf-8 textwidth=79
