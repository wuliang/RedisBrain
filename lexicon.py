# -*- coding: utf8 -*-

import re
import logging
import brain

# If needed, this can be used to check Chinese
#Block                                 Range       Comment
#CJK Unified Ideographs                 4E00-9FFF   Common
#CJK Unified Ideographs Extension A      3400-4DFF   Rare
#CJK Unified Ideographs Extension B      20000-2A6DF Rare, historic
#CJK Compatibility Ideographs            F900-FAFF   Duplicates, unifiable variants, corporate characters
#CJK Compatibility Ideographs Supplement 2F800-2FA1F Unifiable variants

# default delimiters for splitSentence
# # is the reserved word in the system

default_delimiters = set(u"""#\n\r\t ,.:?!"()[]{}。，、；：？！“”「」『』《》〈〉【】〖〗〔〕«»─（）﹝﹞…﹏＿‧""")

eng_term_pattern = """[a-zA-Z0-9\\-_']+"""

def should_ignore(char):
    '''
    + ver1
    CJK  Extension B/C
    CJK Compatibility Ideographs
    http://www.unicode.org/charts/
    + ver2
    \u4e00-\u9fff
    '''
#    # cjk compatibility ideographs
#    if char > u'\uffff' or u'\uf900' <= char <= u'\ufaff':
#        return True
#    else:
#        return False
    # Ver2
    if  u'\u4e00' <= char <= u'\u9fff':
        return False
    else:
        return True
        
def splitNgrams(n, terms):

    for i in xrange(len(terms) - n + 1):
        yield terms[i:i+n]

def iterEnglishTerms(text):

    terms = []
    parts = text.split()
    for part in parts:
        for term in re.finditer(eng_term_pattern, part):
            terms.append(term.group(0))
    return terms

def iterMixTerms(text, eng_prefix='E'):
    # last position term
    terms = []
    parts = text.split()
    for part in parts:
        last = 0
        for match in re.finditer(eng_term_pattern, part):
            previous_term = part[last:match.start()]
            if previous_term:
                terms.append(previous_term)
            if eng_prefix:
                terms.append(eng_prefix + match.group(0).lower())
            else:
                terms.append(match.group(0).lower())
            last = match.end()
        final_term = part[last:]
        if final_term:
            terms.append(final_term)
    return terms

def splitSentence(text, delimiters=None):

    if delimiters is None:
        delimiters = default_delimiters

    sentence = []
    for c in text:
        if c in delimiters:
            yield ''.join(sentence)
            sentence = []
        else:
            if should_ignore(c):
                continue
            sentence.append(c)
    yield ''.join(sentence)

def iterSentenceRela2(maxn, text):

    for sentence in splitSentence(text):
        terms = []
        # 0 < s1 < e1 < s2 < e2 < len
        # term = (s, e). And s is closed, e is opend
        ext = len(sentence)
        for s1 in xrange(ext):
            for e1 in xrange(s1+1, min(s1+maxn+1, ext+1)):
                for s2 in xrange(e1, ext):
                    for e2 in xrange(s2+1, min(s2+maxn+1, ext+1)):
                        terms.append((sentence[s1:e1], sentence[s2:e2]))
        yield terms


def iterSentenceTerms(maxn,text):

    for sentence in splitSentence(text):
        terms = []
        for n in xrange(1, maxn+1):
            terms.extend(splitNgrams(n, sentence))
        yield terms

def LexiconIterTerms(n, text, emmit_head_tail=False):
    
    for sentence in splitSentence(text):
        first = True
        term = None
        for term in splitNgrams(n, sentence):
            term = term.lower()
            yield term
            if first:
                if emmit_head_tail:
                    yield 'B' + term
                first = False
        if term is not None:
            if emmit_head_tail:
                yield 'E' + term


def LexiconBuilder(text,  n):
    terms_count = {}

    for term in LexiconIterTerms(n, text):
        terms_count.setdefault(term, 0)
        terms_count[term] += 1
    
    return terms_count

def LexiconLine(text):
    return splitSentence(text, delimiters="\r\n")

def LexiconSentence(text):
    return splitSentence(text)
    
