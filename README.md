# inx-pathops

Inkscape extension to apply a path operation multiple times to a
selection of objects.

## Basic usage

This extension takes a selection of a path and a group of elements, or
several elements (paths, shapes, text), and applies a path operation
with the top-most path in the Z-order, and each selected path or each
child of a selected group underneath.

## Background

**inx-pathops** is a rewrite of an extension originally authored by Ryan
Lerch
([**inkscape-extension-multiple-difference**](https://github.com/ryanlerch/inkscape-extension-multiple-difference))
and later expanded in a fork by Maren Hachmann
([**inkscape-extensions-multi-bool**](https://gitlab.com/Moini/inkscape-extensions-multi-bool)).

The rewrite started with the interest to improve overall performance:
* **Responsiveness**: Support of groups (one level, or unlimited nested
levels) was implemented, which can reduce response times because a large
number of elements can be passed from inkscape to the extension script
with just the reference to the id(s) of one or several selected group(s).
* **Z-sorted list** of elements: The Z-sorting of the selected
elements to be processed is done internally in python (using zSort from
pathmodifier) instead of spawning a separate inkscape process.
* **OSError: `Argument list too long`**: Applying the path operation on
a huge number of elements creates a command with a long list of
arguments to spawn a second inkscape process. This can hit
(OS-dependent) limits and cause the extension to fail. ***inx-pathops***
splits the list of elements into smaller 'chunks' (based on a
user-defined max count), and spawns a series of inkscape commands, one
for each chunk.
* **Maintenance**: a single python script and several INX files are used
to provide access to the supported path operations. ***inx-pathops***
offers a combined dialog with additional options, as well as a separate
INX file for each path operation which allows direct application without
a dialog (each can be assigned a custom keyboard shortcut if frequently
used).


## Installation

Copy the files in the `src/` directory into the user extensions
directory (see 'Inkscape Preferences > System' for the exact location)
and relaunch Inkscape.

### The extensions will be available as:

**Extensions > Generate from Path:**
- PathOps...

**Extensions > Generate from Path > PathOps:**
- 1 Union
- 2 Difference
- 3 Intersection
- 4 Exclusion
- 5 Division
- 6 Cut Path
- 7 Combine


## Source

The extension is developed and maintained in:  
https://gitlab.com/su-v/inx-pathops

A ZIP archive of recent snapshot also be downloaded here:  
*(Not available yet)*


## License

GPL-2+
