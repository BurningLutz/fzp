# ============================================================================
# FILE: matcher_multihead.py
# AUTHOR: BurningLutz <lutz.l.burning@gmail.com>
# License: MIT license
# ============================================================================

import re
from functools import partial, reduce

from deoplete.filter.base import Base

_re_splitter = re.compile(
    r'[0-9]+|[A-Z]+(?=[A-Z][a-z]|[^a-zA-Z]|$)|[A-Z][a-z]+|[a-z]+'
)


def pipe(x, *fs):
    return reduce(lambda x, f: f(x), fs, x)


def split_words(s):
    return [x.span() for x in _re_splitter.finditer(s)]


def match(words_pos, cand, comp, ignorecase):
    first_matched_pos_idx = next((i for i, x in enumerate(words_pos) if (
        not ignorecase and comp[0] == cand[x[0]]
        or ignorecase and comp[0] == cand[x[0]].lower()
    )), None)

    if first_matched_pos_idx is None:
        return None

    first_matched_pos = words_pos[first_matched_pos_idx]
    cur_comp = 1
    cur_cand = first_matched_pos[0] + 1

    while (
        cur_comp < len(comp)
        and cur_cand < first_matched_pos[1]
        and (
            not ignorecase and comp[cur_comp] == cand[cur_cand]
            or ignorecase and comp[cur_comp] == cand[cur_cand].lower()
        )
    ):
        cur_cand += 1
        cur_comp += 1

    if cur_comp == len(comp):
        return (first_matched_pos[0],)

    while cur_comp >= 0:
        rest = match(words_pos[first_matched_pos_idx+1:], cand, comp[cur_comp:], ignorecase)

        if rest is not None:
            return (first_matched_pos[0],) + rest

        cur_comp -= 1

    return None


def cmpkey(xs):
    return pipe(
        xs,
        lambda x: x[0],
        partial(map, str),
        ''.join,
    )


def match_candidate(cand, comp, ignorecase):
    return match(split_words(cand['word']), cand['word'], comp, ignorecase)


class Filter(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'matcher_multihead'
        self.description = 'multi-head matcher'

    def filter(self, context):
        complete_str = context['complete_str']
        candidates = context['candidates']
        ignorecase = context['ignorecase']

        if not complete_str:
            return context['candidates']

        if ignorecase:
            complete_str = complete_str.lower()

        return pipe(
            candidates,
            partial(map, lambda x: (match_candidate(x, complete_str, ignorecase), x)),
            partial(filter, lambda x: x[0] is not None),
            partial(sorted, key=cmpkey),
            partial(map, lambda x: x[1]),
            list,
        )
