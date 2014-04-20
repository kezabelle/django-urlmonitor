# -*- coding: utf-8 -*-


def hasattrs(thing, *args):
    found_attrs = set()
    for attrib in args:
        if hasattr(thing, attrib):
            found_attrs.add(attrib)
    return found_attrs


def maybecallattr(thing, attr, *callargs, **callkwargs):
    new_attr = getattr(thing, attr, None)
    # if they're methods (which they usually are) then try and call them.
    if new_attr is not None and callable(new_attr):
        new_attr = new_attr(*callargs, **callkwargs)
    return new_attr
