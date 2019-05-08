#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals, print_function
import logging
import argparse
import os
import sys
import codecs
import foma
import json
import copy
from collections import Counter


if sys.version_info < (3, 0):
    sys.stderr = codecs.getwriter('UTF-8')(sys.stderr)
    sys.stdout = codecs.getwriter('UTF-8')(sys.stdout)
    sys.stdin = codecs.getreader('UTF-8')(sys.stdin)



"""
Module for XXX


see docs for Python API functions
https://github.com/simon-clematide/foma/blob/master/python/foma.pyx



    def med(self, word, int limit=4, int cutoff=15,
            int heap_max=4194305, align=None):
        if not self.arity == 1:
            raise NotImplementedError('miminum edit distance is only supported for FSAs')
        cdef apply_med_handle* medh = apply_med_init(self.net)
        apply_med_set_med_limit(medh, limit)
        apply_med_set_med_cutoff(medh, cutoff)
        apply_med_set_heap_max(medh, heap_max)
        if align:
            align = as_str(align)
            apply_med_set_align_symbol(medh, align)
        word = as_str(word)
        cdef char* result = apply_med(medh, word)
        cdef int cost
        cdef char *instring, *outstring
        try:
            while True:
                if result == NULL: break
                cost = apply_med_get_cost(medh)
                instring = apply_med_get_instring(medh)
                outstring = apply_med_get_outstring(medh)
                yield MEDMatch(cost, instring, outstring)
                result = apply_med(medh, NULL)
        finally:
            free(medh)


<class 'foma.MEDMatch'> ['__class__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', 'cost', 'instring', 'outstring']



foma[0]: help med
##
apply med <string>              find approximate matches to string in top network by minimum edit distance
Short form: med <string>

##
apply med                       enter apply med mode (Ctrl-D exits)
Short form: med

##
variable med-limit              the limit on number of matches in apply med
Default value: 3

##
variable med-cutoff             the cost limit for terminating a search in apply med
Default value: 3
"""

def med(fsm, options):
    """Return list of unique instring, outstring, editdist tupels"""
    stats = Counter()
    results = []
    seen_wf = set()
    for wf in sys.stdin:
        wf = wf.rstrip()
        if wf in seen_wf:
            continue
        else:
            seen_wf.add((wf,))
            stats["WFs"] += 1
    word_results = set()
    for result in fsm.med_words(list(seen_wf),limit=options.limit,cutoff=options.cost_cutoff,align=options.align_character):
        if str(result.outstring) not in word_results:
#           print(type(result),dir(result),flush=True)
            results.append((str(result.instring), str(result.outstring), int(result.cost)))
            print(result.instring, result.outstring, result.cost, flush=True)
            word_results.add(str(result.outstring))
            stats['EDs'] += 1

    print(stats, file=sys.stderr)
    return results

def med_file(fsm, options):
    """Return list of unique instring, outstring, editdist tupels"""
    stats = Counter()
    results = []
    seen_wf = set()
#     for wf in sys.stdin:
#         wf = wf.rstrip()
#         if wf in seen_wf:
#             continue
#         else:
#             seen_wf.add((wf,))
#             stats["WFs"] += 1
    word_results = set()
    for result in fsm.med_words(options.filename,limit=options.limit,cutoff=options.cost_cutoff,align=options.align_character):
        if str(result.outstring) not in word_results:
#           print(type(result),dir(result),flush=True)
            results.append((str(result.instring), str(result.outstring), int(result.cost)))
            print(result.instring, result.outstring, result.cost, flush=True)
            word_results.add(str(result.outstring))
            stats['EDs'] += 1

    print(stats, file=sys.stderr)
    return results

# def med(fsm, options):
#     """Return list of unique instring, outstring, editdist tupels"""
#     stats = Counter()
#     results = []
#     seen_wf = set()
#     origfsm = copy.deepcopy(fsm)
#     for wf in sys.stdin:
#         wf = wf.rstrip()
#         if wf in seen_wf:
#             continue
#         else:
#             seen_wf.add((wf,))
#             stats["WFs"] += 1
#         word_results = set()
#         for result in fsm.med(wf,limit=min(options.limit,len(wf)),cutoff=options.cost_cutoff,align=options.align_character,heap_max=2000):
#             if str(result.outstring) not in word_results:
# #           print(type(result),dir(result),flush=True)
#                 results.append((str(result.instring), str(result.outstring), int(result.cost)))
#                 print(result.instring, result.outstring, result.cost, flush=True)
#                 word_results.add(str(result.outstring))
#                 stats['EDs'] += 1
#         fsm.__dealloc__()
#         fsm = copy.deepcopy(origfsm)
#     print(stats, file=sys.stderr)
#     return results



def to_json(result):
    """Return json representation of

    Dict of word form => Dict of Edit Distance => list of strings

{
  "krauteren": [
    {
      "d": 1,
      "w": [
        "krateren",
        "krauterer"
      ]
    },
    {
      "d": 2,
      "w": [
        "kratere",
        "kratern",
        "krauter",
        "krautesel",
        "kräuterin",
        "kräutern"
      ]
    }
  ]
}

$ mypy -c 'reveal_type({"krauteren": [{"d": 1, "w": ["krateren", "krauterer"]}, {"d": 2, "w": ["kratere", "kratern", "krauter", "krautesel", "kräuterin", "kräutern"]}]})'
<string>:1: error: Revealed type is 'builtins.dict[builtins.str*, builtins.list*[builtins.dict*[builtins.str, builtins.object]]]'


    """
    json_result = {}
    for (instring, outstring, editdistance ) in result:

        instring_dict = json_result.setdefault(instring,{})
        instring_dict_edit_list = instring_dict.setdefault(editdistance,[])
        instring_dict_edit_list.append(outstring)
    for edits in json_result.values():
        for cands in edits.values():
            cands.sort()
    for wf,edits in json_result.items():
        editdicts = []
        for e,l in edits.items():
            editdicts.append({"d":e,"w":l})
        json_result[wf] = editdicts

    return json_result


def process(options):
    """
    Do the processing
    """
    fsm = foma.read_binary(options.automaton)
    print('#INFO Loaded automaton %s' %options.automaton, file=sys.stderr)

    if options.filename is not None:
        results = med_file(fsm, options )
        print(results)
        return
    results = med(fsm, options)
    if 'l' in options.mode:
        for r in results:
            print("\t".join(r))
    elif 'j' in options.mode:
        jsonresult = to_json(results)
        print(json.dumps(jsonresult, ensure_ascii=False,sort_keys=True))


def main():
    """
    Invoke this module as a script
    """
    parser = argparse.ArgumentParser(
        usage = '%(prog)s [OPTIONS] ',
        description='Calculate something',
        epilog='Contact simon.clematide@uzh.ch'
        )
    parser.add_argument('--version', action='version', version='0.99')
    parser.add_argument('-l', '--logfile', dest='logfile',
                      help='write log to FILE', metavar='FILE')
    parser.add_argument('-q', '--quiet',
                      action='store_true', dest='quiet', default=False,
                      help='do not print status messages to stderr')
    parser.add_argument('-d', '--debug',
                      action='store_true', dest='debug', default=False,
                      help='print debug information')
    parser.add_argument('-L', '--limit',
                      action='store', dest='limit', default=20,type=int,
                      help='set maximum distance in absolute (default 20)')
    parser.add_argument('-C', '--cost_cutoff',
                      action='store', dest='cost_cutoff', default=10,type=int,
                      help='set maximum distance in absolute (default 10)')
    parser.add_argument('-A', '--align_character',
                      action='store', dest='align_character', default=None,
                      help='character for alignment indication (default None)')
    parser.add_argument('-a', '--automaton', dest='automaton',
                      help='binary foma automaton file', metavar='FILE', default='')
    parser.add_argument('-m', '--mode', dest='mode',
                      help='output mode: l=list j=json format', metavar='Mode', default='l')
    parser.add_argument('-i', '--filename', dest='filename',
                      help='input filename', metavar='FILE', default=None)
    parser.add_argument('args', nargs='*')
    options = parser.parse_args()
    if options.logfile:
        logging.basicConfig(filename=logfile)
    if options.debug:
        logging.basicConfig(level=logging.DEBUG)

    process(options)


if __name__ == '__main__':
    main()
