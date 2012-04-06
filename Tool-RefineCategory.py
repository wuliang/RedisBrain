# -*- coding: utf8 -*-
import sys
import redis
import brain as BBRR
import lexicon
import utils 
import codecs

def main():
    if len(sys.argv) < 3:
        print "Usage:",  sys.argv[0],  "category  type\n\r"
        print "please check you parameters. current number is %d" % (len(sys.argv) - 1)
        print "support type: rela, dist, find, seg"
        return

    category = sys.argv[1]
    type = sys.argv[2]
    
    if category != "test" and type != "find":
        print "Please Check category or modify source code."
        return

    if type not in ['rela', 'dist',  'find',  'seg']:
        print "Unsupported Type"
        return
    
    ngram = 3
    r = redis.Redis(host='localhost', port=6379, db=11)
    brain = BBRR.Brain(r,  "abcLEX",  ngram)
   
    cat = brain.fetchCategory(category)
    if cat:
        if type == 'rela':
            cat.refineRela()
        elif type =='dist':
            cat.refineDist()
        elif type == 'find':
            atom = sys.argv[3]
            print utils.collection_str(cat.findAtom(atom))
        elif type == 'seg':
            filename = sys.argv[3]
                    
            text_file = codecs.open(filename, 'rt', encoding='utf8')
            text_read = text_file.read()  
            for sentence in cat.segment_txt(text_read):
                print sentence[0] 

if __name__ == '__main__':
    main()
    
