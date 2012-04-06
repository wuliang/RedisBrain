# -*- coding: utf8 -*-
import redis
import brain as BBRR
import lexicon
import utils 

def main():
    
    r = redis.Redis(host='localhost', port=6379, db=11)
    #r.flushdb()
    # A
    brain = BBRR.Brain(r,  "haha",  2)
    brain.fetchCategory("ABCD")
    brain.fetchCategory("ABCD")
    brain.fetchCategory("HIJ")
    brain.fetchCategory("KLM")
    print brain.getCategoryList()
    print brain.getCategoryScoreList()
    print brain.getCategoryNameScoreList()
    
    brain.addCategory("KLM")
    brain.addCategory("KLM")
    brain.addCategory("KLM")
    print brain.getCategoryList()
    print brain.getCategoryScoreList()
    print brain.getCategoryNameScoreList()
    #print brain.category.grp_get_score("ABCD")
    #print brain.category.grp_get_score("HIJ")
    #print brain.category.grp_get_score("KLM")
    testtxt = u"这是一个这是测试程序程序啊程序这是这是这这这。"
    brain.feed_plain_txt(testtxt, 'test',  1)
    cat = brain.fetchCategory('test')
    print utils.collection_str(cat.getAtomNameScoreList())
    print "=" * 80
    print utils.collection_str(cat.getAtomNameScoreList(n=1))
    print brain.getInfo()

if __name__ == '__main__':
    main()
    
