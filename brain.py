# -*- coding: utf8 -*-
import random
import redis
import lexicon
import exceptions
import utils
 
class GroupType():
    def __init__(self,  std_num, delta):
        self.std_num = std_num
        self.delta = delta
        self.max_num = (int)(self.std_num * self.delta)
        
    def Scale(self,  times):
        self.std_num = self.std_num * times
        self.max_num = (int)(self.std_num * self.delta)
        
BASIC_ATOM_GROUP_TYPE = GroupType(5000,  1.1)
BASIC_RELATION_GROUP_TYPE = GroupType(1000000,  1.2)
BASIC_STATIC_GROUP_TYPE = GroupType(100000000,  1.3) # nearly never rebuild

class Group():
    
    def __init__(self, redis, name, type):
        self.redis = redis
        self.name = name
        self.type = type

    def grp_item_del(self,  item):
        name = self.name
        self.redis.zrem(name, item)
        
    def grp_item_add(self, item, amount=1):
        name = self.name
        self.redis.zincrby(name, item, amount=amount)
        len = self.redis.zcard(name) 
        if (len > self.type.max_num):
            cutnum = int(random.triangular(1,  len - self.type.std_num)) # triangular -> randint ? 
            if 1 <= cutnum <= len - self.type.std_num:
                self.redis.zremrangebyrank(name, 0, cutnum-1) 
                len = self.redis.zcard(name)
            else:
                raise exceptions.Exception("%s random error !" % self.name)                
        return len

    def grp_item_add_with_score(self, item, score):
        name = self.name
        self.redis.zadd(name, value,  score)
        len = self.redis.zcard(name) 
        if (len > self.type.max_num):
            cutnum = int(random.triangular(1,  len - self.type.std_num)) # triangular -> randint ?
            if 1 <= cutnum <= len - self.type.std_num:            
                self.redis.zremrangebyrank(name, 0, cutnum-1) 
                len = self.redis.zcard(name)            
            else:
                raise exceptions.Exception("%s random error !" % self.name)
        return len
        
    def grp_len(self):
        name = self.name
        return self.redis.zcard(name)
    
    def grp_get_score(self,  item):
        name = self.name
        return self.redis.zscore(name,  item)

    def grp_get_real_range(self,  start,  end):
        len = self.redis.zcard(self.name)   
        if len == None:
            raise exceptions.Exception("Get range for category %s length is zero!" % self.name)
        
        if start == None:
            start = 0
        if end == None:
            end = len - 1
            
        if start < 0:
            start = start + len
        if end < 0:
            end = end + len
            
        #if end < start:
        # let it be, let the caller get empty list
        return (start,  end)
        
    def grp_get_name_list(self, start=None,  end=None, rev=False):
        r = self.grp_get_real_range(start,  end)
        if not rev:
            return self.redis.zrange(self.name, r[0], r[1], withscores=False)
        else:
            return self.redis.zrevrange(self.name, r[0], r[1], withscores=False)            

    def grp_get_name_score_list(self, start=None,  end=None, rev=False):
        r = self.grp_get_real_range(start,  end)
        if not rev:
            return self.redis.zrange(self.name, r[0], r[1], withscores=True)
        else:
            return self.redis.zrevrange(self.name, r[0], r[1], withscores=True)            

    def grp_get_score_list(self, start=None,  end=None, rev=False): 
        return [x[1] for x in self.grp_get_name_score_list(start=start,  end=end, rev=rev)] 
        
class CombinedGroup():
    
    def __init__(self, description):
        self.description = description
        self.fields = {}
        for key in description:
            self.fields[key[key.find(':')+1:]] = description[key]
            
        basekeys = [key[:key.rfind(':')] for key in description]
        if basekeys:
            base = basekeys[0]
            for key in basekeys:
                if key != base:
                    raise exceptions.Exception("%s base name error ! want %s" % (key,  base))   
        else:
            raise exceptions.Exception("no description provided for CombinedGroup")
    
    def grp_item_del(self,  item):
        for f in fields:
            fields[f].grp_item_del(item)

    def grp_get_score(self,  item):
        dict = {}
        for f in fields:
            dict[f] = fields[f].grp_get_score(item)
        return dict
            
    def grp_item_add(self, item, amounts):
        count = 0
        min = 0
        for f in fields:
            len = fields[f].grp_item_add(item,  amounts[f])
            if count  == 0:
               min = len
            else:
                if len < min:
                    min = len 
            count += 1
        return min

    def grp_item_add_with_score(self, item, scores):
        count = 0
        min = 0
        for f in fields:
            len = fields[f].grp_item_add_with_score(item,  scores[f])
            if count  == 0:
               min = len
            else:
                if len < min:
                    min = len 
            count += 1
        return min
        
class Category():

    def __init__(self, brain, redis, name, ngram):
        self.brain = brain
        self.redis = redis
        self.name = name
        self.ngram = ngram
        self.ngrams = {}
        self.grpid = 0
        self.grpmap = {}
        self.grpnames = {} 
        self.scale = 1
        # special for dictionary category
        if "child" in name:
            self.ngram = 8
            self.scale = 100
            
        scale = self.scale
        type_short = BASIC_ATOM_GROUP_TYPE
        type_short.Scale(scale)
  
        type_long = BASIC_RELATION_GROUP_TYPE
        type_long.Scale(scale)
        
        for n in xrange(self.ngram+1):
            # 0 is a collection of all ngrams
            groupname = self.name + ":gram:" + str(n+1)
            id = self.fetchGrpId(groupname)
            self.ngrams[id] = Group(self.redis,  groupname, type_short )

        groupname = self.name + ":meta:sum"
        id = self.fetchGrpId(groupname)
        self.gram_sum = self.ngrams[id] = Group(self.redis, groupname,  type_short)

        groupname = self.name + ":meta:variety"
        id = self.fetchGrpId(groupname)
        self.gram_variety = self.ngrams[id] = Group(self.redis, groupname,  type_short)

        groupname = self.name + ":rela2"
        id = self.fetchGrpId(groupname)
        self.relation2 = self.ngrams[id] = Group(self.redis, groupname,  type_long)
    
        # dist related (for a ngram)
        for n in xrange(self.ngram+1):
            basename = self.name + ":dist:" + str(n+1) 
            # E (average)
            groupname = basename + "X"
            id = self.fetchGrpId(groupname)
            self.dist_x = self.ngrams[id] = Group(self.redis, groupname,  type_short)
        
        groupname = self.name + ":static"
        id = self.fetchGrpId(groupname)
        self.static = self.ngrams[id] = Group(self.redis, groupname,  type_short)

    # this should not be a frequently invoked
    def fetchGrpId(self, name):
        id = self.grpmap.setdefault(name,  self.grpid) 
        self.grpnames[id] = name
        if id == self.grpid:
            self.grpid += 1
        return id
        
    # it is short name from outside     
    def findGrpbyName(self, name):
        name = ":".join([self.name, name])
        if name not in self.grpmap:
            return None
        return self.grpmap[name]
        
    def findAtom(self, atom):
        finds = []
        for n in xrange(1,  self.ngram+1):
            for name, score in self.getAtomNameScoreList(n,  rev=True):
                if name.find(atom) != -1:
                    finds.append((name,  score))
        return finds
                
    def refineDist(self):
        n=1 # This function is in testing.
        for atom, score0 in self.getAtomNameScoreList(n, rev=True):
            left = []
            right = []
            alen = len(atom)
            for name, score in self.getAtomNameScoreList(n+1,  rev=True):
                nlen = len(name)
                if nlen <= alen:
                    continue

                if name.find(atom) == 0:
                    left.append(score)
                    
                if name.rfind(atom) == nlen-alen:               
                    right.append(score)
            all = left + right   
            left.sort()
            right.sort()
            all.sort()
            sum_left = sum(left)
            sum_right = sum(right)
            sum_all = sum(all)
            print "\n====\n%s:" % atom
            print "total: %d %d %f" % (score0, sum_all,  sum_all/score0)
            print "A-len %d sum %d" % (len(all), sum_all)
            if left:
                print "m: %d, v %d" % utils.stat(all)
            print "*" * 20                
            print "L-len %d sum %d" % (len(left), sum_left)
            if left:
                print "m: %d, v %d" % utils.stat(left)
            print "*" * 20
            print "R-len %d sum %d" % (len(right), sum_right)
            if right:
                print "m: %d, v %d" % utils.stat(right)


#        left_means = kmeans(left,  5)                
#        for left_one in left_means:
#            print left_one
#            print sum(left_one)
#            print "m: %d, v %d" % stat(left_one)
#        print "=" * 80
#
#        print sum(right)
#        print "m: %d, v %d" % stat(right)
#        right_means = kmeans(right,  5)
#        for right_one in right_means:
#            print right_one
#            print sum(right_one)
#            print "m: %d, v %d" % stat(right_one)
        
            
                        
    def refineRela(self):
        '''
        remove relation which has already included in ngram list
        (in other word, use ngram to manage this relation)
        '''
        fetch_num = 5000
        deleted  = 0
        cur = 0

        while True:
            fetched = self.relation2.grp_get_name_score_list(start=cur,  end=cur+fetch_num-1, rev=True)
            items = []            
            for item, score in fetched:
                idx = item.find('#')
                if idx == -1:
                    continue
                realname = item[:idx] + item[idx+1:]
                gram = self.ngrams[0].grp_get_score(realname)
                if gram:
                    items.append(item)              
            for item in items:
                self.relation2.grp_item_del(item)
            cur = cur + fetch_num - len(items)
            deleted = deleted + len(items)
            total = self.relation2.grp_len()
            if cur >= total:
                break
            print "Total %d, Current %d, Deleted %d" % (total,  cur,  deleted)
        
    def addAtom(self, atom, n, delta=1):
        self.ngrams[n].grp_item_add(atom, amount=delta)

    def addGramSum(self, n, delta=1):
        self.gram_sum.grp_item_add(n, amount=delta)

    def addGramVariety(self, n, delta=1):
        self.gram_variety.grp_item_add(n, amount=delta)
        
    def getAtom(self, atom, n=0):
        return self.ngrams[n].grp_get_score(atom)

    def getAtoms(self, *atoms):
        return [self.getAtom(atom) for atom in atoms]

    def getGramLen(self, n=0):
        return self.ngrams[n].grp_len()
        
    def getGramSum(self, n=0):
        return self.gram_sum.grp_get_score(n)

    def getGramVariety(self, n=0):
        return self.gram_variety.grp_get_score(n)

    def getAtomList(self, n=0, start=None,  end=None, rev=False):
        return self.ngrams[n].grp_get_name_list(start=start,  end=end,  rev=rev)

    def getAtomScoreList(self, n=0, start=None,  end=None, rev=False):
        return self.ngrams[n].grp_get_score_list(start=start, end=end, rev=rev)

    def getAtomNameScoreList(self, n=0, start=None,  end=None, rev=False):
        return self.ngrams[n].grp_get_name_score_list(start=start,  end=end, rev=rev)
        
    def getInfo(self):
        info_str = "Category:%s[%d]\n\r" % (self.name,  self.ngram)
        info_str = info_str + "groups:\n"
        for s,  v in self.grpnames.items():
            info_str = info_str + "\t(%d)%s\n" % (s,  v)
            
        for n in range(self.grpid):
            a,  b,  c = self.getGramSum(n),  self.getGramVariety(n), self.getGramLen(n)
            if not a:
                a = 0
            if not b:
                b = 0
            if not c:
                c = 0
            nstr = "[%d] S=%d, V=%d, Len=%d\n\r" %(n, a, b, c)
            info_str = info_str + nstr
        info_str = info_str + "\n\r\n\r"
        return info_str

    def splitTerms(self, text):
        grams = []
        for n in xrange(1, self.ngram+1):
            ngrams = []
            sum = self.getGramSum(n)

            for atom in lexicon.LexiconIterTerms(n, text):
                score = self.getAtom(atom,  n=n)
                if not score or not sum:
                    p = 0
                else:
                    p = score/sum
                    #print "score is %d, %d, %f" % (score,  sum,  p)
                ngrams.append((atom, p))
            grams.append(ngrams)
        return grams

        
    # i don't want to feed all n < n-grams, just this one by one
    def feed_plain_txt(self,  txt, ngram):
        sum = 0
        variety =0
        atom_count = lexicon.LexiconBuilder(txt,  ngram)
        for atom, delta in atom_count.iteritems():
            sum += delta
            variety += 1

            self.addAtom(atom, ngram, delta=delta)
            self.addAtom(atom, 0, delta=delta)
            
        self.addGramSum(ngram,  delta=sum)
        self.addGramSum(0,  delta=sum)
        
        self.addGramVariety(ngram,  delta=variety)
        self.addGramVariety(0,  delta=variety) 
        

    def feed_relation_plain_txt(self,  txt):
        for termlist in lexicon.iterSentenceRela2(2, txt):
            for s1,  s2 in termlist: 
                atom = s1 + "#" + s2
                self.relation2.grp_item_add(atom, amount=1)
            

    def feed_dict_txt(self,  txt):
        myshort = self.brain.getCetegoryShortname(self.name)
        child = self.brain.fetchCategory(myshort + ":child")
        counts = {}
        for n in xrange(1,  child.ngram+1):
            counts[n] = 0
            
        for atom in lexicon.LexiconLine(txt):
            la = len(atom)
            if  la == 0 or la > child.ngram:
                continue #raise exceptions.Exception("bad Lexicon processing.")   
            counts[la] += 1
            child.addAtom(atom, la, delta=1)
            child.addAtom(atom, 0, delta=1)              
                
        for n in xrange(1,  child.ngram+1):          
            child.addGramSum(la,    delta=counts[la])
            child.addGramSum(0,     delta=counts[la])        
            child.addGramVariety(la,  delta=counts[la])
            child.addGramVariety(0,   delta=counts[la]) 

    def segment_txt(self,  txt):
        result_txt = ""
        myshort = self.brain.getCetegoryShortname(self.name)
        child = self.brain.findCategory(myshort + ":child")     

        for setence in lexicon.LexiconSentence(txt):
            if len(setence) == 0:
                continue #raise exceptions.Exception("bad Lexicon processing.")
            yield self.getSegment(setence, child)


    def getSegment(self, text, child):

        def _getCandidate(i, left, right):
            left_range = (i, i+left-1)
            right_range = (i+left, i+left+right-1)
            left_item = table[left_range]
            right_item = table[right_range]
            return ("("+ left_item[0]+" "+right_item[0]+")", left_item[1] * right_item[1])

        table = {}    
        grams = self.splitTerms(text)
        n = len(grams)
        size = len(grams[0])
 
 
        for current_size in xrange(1, size+1):
            if child:
                child_sum = child.getGramSum(current_size)
            for i in xrange(size - current_size + 1):                
                candidates = []
                for count in xrange(1, (current_size/2) + 1):
                    left, right = count, current_size - count
                    candidates.append(_getCandidate(i, left, right))
                    if left != right:
                        left, right = right, left
                        candidates.append(_getCandidate(i, left, right))
                if current_size <= n:
                    candidates.append(grams[current_size-1][i])
                # child is the dictionary
                if child and current_size <= child.ngram:
                    str = text[i:current_size+i]

                    score = child.getAtom(str, current_size)
               
                    if score and child_sum:                        
                        p = score/child_sum
                        #print "Have Entry %s %f" % (str,  p)                        
                        candidates.append((str, p))
                candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
                current_range = (i, i+current_size-1)
                table[current_range] = candidates[0]
                #print "Select for range:", current_range, candidates[0][0], candidates[0][1]
                
        return table[(0, size-1)]
        
class Brain():

    def __init__(self, redis, name,  ngram):

        self.redis = redis        
        self.name = name        
        self.ngram = ngram

        groupname = self.name + ":catlist"
        self.category = Group(self.redis, groupname,  BASIC_ATOM_GROUP_TYPE)
        
        self.category_obj = {}
        for cat in self.getCategoryList():
            self.category_obj[cat] = Category(self,  self.redis, self.getCetegoryFullname(cat), self.ngram)
    
    def getCetegoryFullname(self,  name):
        return self.name+":cat:"+name

    def getCetegoryShortname(self,  name):
        prefix = self.name+":cat:"
        return name[name.find(prefix)+len(prefix):]
        
    # It is not a cleaning method, should make full clean in redis-cli
    def deleteCategory(self, name):
        if name in  self.category_obj.keys():
            del  self.category_obj[name]
        self.category.grp_item_del(name)
    
    def findCategory(self, name):
        if name in  self.category_obj.keys():
            return  self.category_obj[name]
        return None
        
    def fetchCategory(self,  name):
        if name in  self.category_obj.keys():
            return  self.category_obj[name]
            
        category = self.getCategory(name)
        if not category:
            self.addCategory(name)
            category = self.getCategory(name)
            if not category:
                raise exceptions.Exception("Fail to create new category %s" % name) 
                
            self.category_obj[name] = Category(self, self.redis, self.getCetegoryFullname(name), self.ngram)            
        else:
            raise exceptions.Exception("DB and memory for category %s is not consistent" % name)
        return  self.category_obj[name]
            
    def addCategory(self, name):
        self.category.grp_item_add(name, amount=1) 
        
    def getCategory(self, name):
        return  self.category.grp_get_score(name)
 
    def getCategoryList(self):
        return self.category.grp_get_name_list()

    def getCategoryScoreList(self):
        return self.category.grp_get_score_list()

    def getCategoryNameScoreList(self):
        return self.category.grp_get_name_score_list()
        
    def getInfo(self):
        info_str = "Brain:%s[%d]\n\r" % (self.name,  self.ngram)
        info_str = info_str + "with Categories: { " + " ,".join(self.category_obj.keys()) + " }\n\r====\n\r"
        for name in self.category_obj.keys():
            catobj = self.category_obj[name]
            info_str = info_str + catobj.getInfo()
        info_str = info_str + "\n\r\n\r"
        return info_str



        

 
