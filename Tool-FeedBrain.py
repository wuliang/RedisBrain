# -*- coding: utf8 -*-
import sys
import redis
import brain as BBRR
import lexicon
import utils 
import codecs

def main():
    if len(sys.argv) < 3:
        print "Usage:",  sys.argv[0],  "filename",   "category",  "[ngram] \n\r"
        print "default value of ngram is 1, only the n equal with 'ngram' will be generated! "
        print "please check you parameters. current number is %d" % (len(sys.argv) - 1)
        return

    filename = sys.argv[1]
    category = sys.argv[2]
    ngram = 1

    if category != "test":
        print "Please Check category or modify source code."
        return
        
    if len(sys.argv) >= 4:
        ngram = int(sys.argv[3])
    if ngram > 4 or ngram < 0:
        # usually not correct
        print "please modify  %s to support this ngram." % sys.argv[0]
        return
    
    r = redis.Redis(host='localhost', port=6379, db=11)
    brain = BBRR.Brain(r,  "abcLEX",  ngram)
    text_file = codecs.open(filename, 'rt', encoding='utf8')
    text_read = text_file.read()
        
    # before 
    print "+" * 80
    print brain.getInfo()
    print "+" * 80

    cat = brain.fetchCategory(category)
    if not cat:
        print "no such category"
        return
        
    if "dict" in filename:
        print "Feed dictionary...."
        cat.feed_dict_txt(text_read)
    else:
        cat.feed_plain_txt(text_read, ngram)

    # After
    print brain.getInfo()    
    print "+" * 80


if __name__ == '__main__':
    main()
    
