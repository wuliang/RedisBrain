# -*- coding: utf8 -*-
import sys
import redis
import brain as BBRR
import lexicon
import utils 
import codecs
import brainsql

def main():
    if len(sys.argv) < 2:
        print "Usage:",  sys.argv[0],  "category",  "[start] [end] \n\r"
        print "please check you parameters. current number is %d" % (len(sys.argv) - 1)
        return

    output = "abcFrequency.db"
    category = sys.argv[1]
    start = None
    end = None

    if category != "test":
        print "Please Check category or modify source code."
        return
        
    if len(sys.argv) >= 3:
        start = int(sys.argv[2])
    if len(sys.argv) >= 4:
        end = int(sys.argv[3])

    # there is no need to check "start <= end", in fact start can be Positive, and end be Negative,  
    # redis accept it.
    

    r = redis.Redis(host='localhost', port=6379, db=11)
    brain = BBRR.Brain(r,  "abcLEX",  2)
    sql = brainsql.BrainSql(output)
   
    # brief 
    print "+" * 80
    print brain.getInfo()
    print "+" * 80
    
    cat = brain.fetchCategory(category)
    if not cat:
        print "Can't find the category %s" % category
        return
        
    fulllist = cat.getAtomNameScoreList(start=start, end=end, rev=True)
    for i, (ch, score) in enumerate(fulllist):
        sql.insert_chinese_frequency(ch,  i)
    sql.commit()
    sql.close()
    print "+" * 80
    

if __name__ == '__main__':
    main()
    
