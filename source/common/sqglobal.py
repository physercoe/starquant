#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import defaultdict


class dotdict(dict):

    """
    dot.notation access to dictionary attributes
    """

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


context = dotdict()


history_bar = defaultdict(list)
history_tick = defaultdict(list)

wxcmd = ''
