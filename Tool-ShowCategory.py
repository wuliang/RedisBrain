# -*- coding: utf8 -*-
import sys
import redis
import brain as BBRR
import lexicon
import utils 
import codecs

def main():
    if len(sys.argv) < 4:
        print "Usage:",  sys.argv[0],  "category", "ngram" , 'grpid',  "[start] [end] \n\r"
        print "please check you parameters. current number is %d\n" % (len(sys.argv) - 1)
        print "if not sure which group to use, use 0 to get a group list"
        return

    category = sys.argv[1]
    ngram = int(sys.argv[2])
    grpid =   int(sys.argv[3])
    start = None
    end = None

    if "test" not in category:
        print "Please Check category or modify source code."
        return
        
    if len(sys.argv) >= 5:
        start = int(sys.argv[4])
    if len(sys.argv) >= 6:
        end = int(sys.argv[5])

    if start==None and end==None:
        # not show full set...since it will block interface
        end = 10
    # there is no need to check "start <= end", in fact start can be Positive, and end be Negative,  
    # redis accept it.
    

    r = redis.Redis(host='localhost', port=6379, db=11)
    brain = BBRR.Brain(r,  "abcLEX",  ngram)
   
    # brief 
    print "+" * 80
    print brain.getInfo()
    print "+" * 80
    
    cat = brain.fetchCategory(category)
    if cat:
        print utils.collection_str(cat.getAtomNameScoreList(n=grpid, start=start, end=end,  rev=True))
    print "+" * 80
        

if __name__ == '__main__':
    main()
    
