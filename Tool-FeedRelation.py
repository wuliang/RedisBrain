# -*- coding: utf8 -*-
import sys
import redis
import brain as BBRR
import lexicon
import utils 
import codecs

def main():
    if len(sys.argv) < 3:
        print "Usage:",  sys.argv[0],  "filename",   "category"
        return

    filename = sys.argv[1]
    category = sys.argv[2]
    ngram = 3

    if category != "test":
        print "Please Check category or modify source code."
        return
        
    r = redis.Redis(host='localhost', port=6379, db=11)
    brain = BBRR.Brain(r,  "abcLEX",  ngram)
    text_file = codecs.open(filename, 'rt', encoding='utf8')
    text_read = text_file.read()
        
    # before 
    print "+" * 80
    print brain.getInfo()
    print "+" * 80
    
    brain.feed_relation_plain_txt(text_read, category)

    # After
    print brain.getInfo()    
    print "+" * 80


if __name__ == '__main__':
    main()
    
