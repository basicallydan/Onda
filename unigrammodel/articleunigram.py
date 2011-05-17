'''
Created on 9 Feb 2010

@author: Daniel Hough
'''

import time

import MySQLdb.cursors
from auxfunctions import database
from auxfunctions import termproc
import clustering
from evaluating import Evaluator
import re
from retrieval import article
from retrieval.article import Article
from stoplist import Stoplist
from term import InvertedIndex
from term import TermList
from threading import Thread

class ArticleModel(object):
    '''
    Represented by a vector
    '''

    def __init__(self, article=None, title_weight=19, leading_weight=1, normalizing_freq=True, stoplist_file=None):
        '''
        An articlemodel has a TermList which counts terms
        '''
        self.article = None
        if article:
            self.article = article
            if(stoplist_file):
                self.stoplist = Stoplist(stoplist_file)
            self.title_weight = title_weight
            self.leading_weight = leading_weight
        self.terms = TermList()
        self.total_term_counts = 0
        self.cluster_id = 0
        self.normalizing_freq = normalizing_freq
    
    def from_db_values(self, db_values):
        # print str(threading.currentThread().getName()) + ": has to load " + str(len(db_values)) + " terms"
        for row in db_values:
            self.from_db_row(row)
        # print str(threading.currentThread().getName()) + ": has finished with loading model of " + str(len(db_values)) + " terms"

    def from_db_row(self, db_row, load_article = True):
        if not self.article and db_row.has_key("articleid") and load_article:
            self.article = Article(id=db_row['articleid'])
            # print "Loaded article with id " + str(db_row['articleid']) + " therefore the article should be set: " + str(self.article)
        if db_row.has_key("term") and load_article:
            self.terms[db_row['term']] = (float(db_row['tf']), int(db_row['count']), None)
        
    def db_load_counts(self, article_id=None, db=None):
        if not self.article and article_id:
            self.article = Article(id=article_id)
            self.terms = TermList()
        if self.article.has_been_counted:
            if not db:
                db = database.connect_to_database()
            cur = db.cursor(cursorclass=MySQLdb.cursors.SSDictCursor)
            query = "SELECT term,tf,count FROM articleswithterms WHERE articleid = %d" % (self.article.id)
            cur.execute(query)
            rows = cur.fetchall()
            self.terms.set_terms([(row['term'], (float(row['tf']), int(row['count']), None)) for row in rows])
            return self.terms.all_terms()
    
    def set_cluster(self, cluster_id, save=False):
        self.cluster_id = cluster_id

    def get_cluster_update_query(self):
        return "UPDATE articles SET `clusterid` = %d WHERE `id` = %d" % (self.cluster_id, self.article.id)

    def db_save_cluster(self):
        db = database.connect_to_database()
        cur = db.cursor()
        cur.execute(self.get_cluster_update_query())
        
    def get_terms(self):
        return self.terms
    
    def set_terms(self, term_list):
        self.terms = term_list
    
    def count_terms(self, normalizing=True):
        re_words = re.compile(r"[a-z]+'?[a-z]+", re.IGNORECASE)
        article_text = termproc.replace_html_chars(self.article.article_text)
        
        terms = re_words.findall(article_text)
        title_terms = re_words.findall(self.article.title)
        
        terms = self.stoplist.apply(terms)
        title_terms = self.stoplist.apply(title_terms)
        
        self.total_term_counts = len(terms) + (len(title_terms) * self.title_weight)
        if not self.normalizing_freq:
            self.denominator = 1
        else:
            self.denominator = len(terms) + (len(title_terms) * self.title_weight)
            # print "Length: " + str(denominator)
        term_indices = xrange(len(terms))
        leading_threshold = 0.02
        leading_threshold = len(terms) * leading_threshold
        for term, i in zip(terms, term_indices):
            if i <= int(leading_threshold):
                weight = self.leading_weight
            else:
                weight = 1
            yield self.terms.count_term(term, self.denominator, weight)
        for term in title_terms:
            yield self.terms.count_term(term, self.denominator, self.title_weight)
            
    def copy(self):
        '''
        Creates an exact copy of the model given, only doesn't take the article
        model also.
        '''
        exact_copy = ArticleModel()
        exact_copy.set_terms(self.terms)
        return exact_copy
    
    def db_save(self, db=None):
        if not db:
            db = database.connect_to_database()
        cur = db.cursor()
        orig_term_inserts = list()
        article_term_inserts = list()
        for term in self.terms:
            tf = self.terms[term][0]
            count = int(self.terms[term][1])
            orig_terms = self.terms[term][2]
            # Check if the stem exists already
            query = "SELECT id FROM unigram_stems WHERE `term` = '" + term + "'"
            cur.execute(query)
            # if the term already exists we update, otherwise insert it
            if db.affected_rows() == 0:
                query = "INSERT INTO unigram_stems (`term`,`totalcount`) VALUES('%s',%d)" % (term, count)
                cur.execute(query)
                term_id = int(cur.lastrowid)
            else:
                row = cur.fetchone()
                term_id = int(row[0])
                query = "UPDATE unigram_stems SET totalcount = totalcount + %d WHERE `id` = %d" % (count, term_id)
                cur.execute(query)
            # Now check if the original terms exist
            for orig_term in orig_terms:
                query = "SELECT * FROM orig_terms WHERE `term` = '%s'" % (orig_term)
                cur.execute(query)
                if db.affected_rows() == 0:
                    orig_term_inserts.append("(%d,'%s')" % (term_id, orig_term))
                    # query = "INSERT INTO orig_terms (`stemid`,`term`) VALUES(%d,'%s')" % (term_id, orig_term)
                    cur.execute(query)
            # Now make the link table row
            article_term_inserts.append("(%d,%d,%d,%.3f)" % (term_id, self.article.id, count, tf))
            # query = "INSERT INTO article_terms (`stemid`,`articleid`,`count`,`tf`) VALUES(%d,%d,%d,%.3f) ON DUPLICATE KEY UPDATE `count` = VALUES(count), `tf` = VALUES(tf)" % (term_id, self.article.id, count, tf)
            # cur.execute(query)

        if len(orig_term_inserts) > 0:
            orig_term_query = "INSERT IGNORE INTO orig_terms (`stemid`,`term`) VALUES %s" % (",".join(orig_term_inserts))
            cur.execute(orig_term_query)
        if len(article_term_inserts) > 0:
            article_term_query = "INSERT INTO article_terms (`stemid`,`articleid`,`count`,`tf`) VALUES %s ON DUPLICATE KEY UPDATE `count` = VALUES(count), `tf` = VALUES(tf)" % (",".join(article_term_inserts))
            cur.execute(article_term_query)
        query = "UPDATE articles SET `counted` = 1 WHERE `id` = %d" % (self.article.id)
        cur.execute(query)
        cur.close()
        db.commit()
    
    def print_terms(self):
        self.terms.print_terms()
    
    def print_info(self):
        print "Article title: " + self.article.title
        print "     UNIQUE TERMS: " + str(len(self.terms))
        print " TOTAL TERM COUNT: " + str(self.total_term_counts)

def db_load_models(articles):
    models = dict()
    inv_index = InvertedIndex()
    num_articles = len(articles)
    db = database.connect_to_database()
    list_of_ids = ",".join([str(article.id) for article in articles])
    query = "SELECT articleid,term,tf,count FROM articleswithterms WHERE articleid IN (%s)" % (list_of_ids)
    cur = db.cursor(cursorclass=MySQLdb.cursors.SSDictCursor)
    num_results = cur.execute(query)
    rows = cur.fetchall()
    model_values = dict()
    for row in rows:
        if model_values.has_key(row['articleid']):
            model_values[row['articleid']].append(row)
        else:
            model_values[row['articleid']] = [row]
    for article, index in zip(articles, xrange(num_articles)):
        if article.has_been_counted:
            print "Loading article " + str(index + 1) + "/" + str(num_articles)
            new_model = ArticleModel(article)
            new_model.from_db_values(model_values[article.id])
            all_terms = new_model.terms.all_terms()
            inv_index.add_term_occurences(all_terms, article.id)
            models[article.id] = new_model
    cur.close()
    db.close()
    return models, inv_index

def count_terms_and_store(articles, store=True, title_weight=19, print_steps=False, leading_weight=1, stoplist_file="../stop_words"):
    if store:
        db = database.connect_to_database()
    models = dict()
    inv_index = InvertedIndex()
    num_articles = len(articles)
    for art, index in zip(articles, xrange(len(articles))):
        if print_steps:
            print "Counting terms of article " + str(index + 1) + "/" + str(num_articles)
        model = ArticleModel(art, title_weight, leading_weight, stoplist_file=stoplist_file)
        for term in model.count_terms():
            inv_index.add_term_ocurrence(term, model.article.id)
        if store:
            model.db_save(db)
        models[art.id] = model
    """ This isn't needed anymore
    total_counts = sum([model.total_term_counts for model in models.values()])
    if store:
        cur = db.cursor()
        query = "UPDATE terms_global SET totaltermcounts = totaltermcounts + %d WHERE id = 1" % (total_counts)
        cur.execute(query)
    """
    return models, inv_index

def test_parameters():
    man_articles = article.db_get_all_articles("NOT trainingcluster = 0")
    flat_thread = EvalThread(clustering.ClusterMaker.FLAT, man_articles, 1)
    # aggl_thread = EvalThread(clustering.ClusterMaker.AGGL,man_articles,2,(19,22),(30,70))
    flat_thread.start()
    # aggl_thread.start()
    '''
    for cl_type,index in zip(clustering.ClusterMaker.cluster_types,xrange(len(clustering.ClusterMaker.cluster_types))):
        eval_thread = EvalThread(cl_type,man_articles,index)
        eval_thread.start()
    '''

class EvalThread(Thread):
    def __init__(self, cluster_type, articles, threadnum, weight_range=(19, 21), thresh_range=(40, 70), l_weight_range=(2, 5)):
        Thread.__init__(self)
        self.cluster_type = cluster_type
        self.articles = articles
        self.threadnum = threadnum
        self.weight_range = weight_range
        self.thresh_range = thresh_range
        self.l_weight_range = l_weight_range
        
    def run(self):
        time_taken = dict()
        i = 1
        for cl_method in clustering.ClusterMaker.cluster_methods:
            for t_weight in range(self.weight_range[0], self.weight_range[1]):
                print "Thread " + str(self.threadnum) + " counting terms..."
                models, inv_index = count_terms_and_store(self.articles, store=False, title_weight=t_weight)
                for l_weight in range(self.l_weight_range[0], self.l_weight_range[1]):
                    for thresh in range(self.thresh_range[0], self.thresh_range[1], 10):
                        print ">>=====Test " + str(i) + " of thread " + str(self.threadnum) + " commencing=====<<"
                        thresh = float(thresh) / 100
                        print "=====Settings for test " + str(i) + "====="
                        print "Cluster type:     " + str(clustering.ClusterMaker.cluster_types[self.cluster_type])
                        print "Cluster method:   " + str(clustering.ClusterMaker.cluster_methods[cl_method])
                        print "Title weight:     " + str(t_weight)
                        print "Leading weight:   " + str(l_weight)
                        print "Threshold:        " + str(thresh)
                        clusterer = clustering.ClusterMaker(cluster_type=self.cluster_type)
                        t1 = time.time()
                        print "Clustering articles..."
                        clusters, models = clusterer.cluster_articles(models, inv_index, threshold=thresh, cluster_method=cl_method)
                        t2 = time.time()
                        evaluator = Evaluator()
                        print "Rand Index:   " + str(evaluator.rand_index(clusters, models))
                        print "        TP:   " + str(evaluator.totaltruepos)
                        print "        TN:   " + str(evaluator.totaltrueneg)
                        print "        FP:   " + str(evaluator.totalfalsepos)
                        print "        FN:   " + str(evaluator.totalfalseneg)
                        print "F-measure:    " + str(evaluator.f_measure(4))
                        print "Purity:       " + str(evaluator.purity(clusters, models))
                        print "NMI:          " + str(evaluator.nmi(clusters, models))
                        time_taken[i] = (t2 - t1)
                        print "Time elapsed: " + str(time_taken[i])
                        print "Saving..."
                        evaluator.db_save(thresh, t_weight, l_weight, clustering.ClusterMaker.cluster_types[self.cluster_type], clustering.ClusterMaker.cluster_methods[cl_method], time_taken[i])
                        i += 1
        print "Thread " + str(self.threadnum) + " complete, " + str(i) + " tests"
                    
if __name__ == '__main__':
    # test_parameters()
    t1 = time.time()
    man_articles = article.db_get_all_articles()
    models, inv_index = db_load_models(man_articles)
    # models, inv_index = count_terms_and_store(man_articles, store=True, title_weight=19, print_steps=True)
    clusterer = clustering.ClusterMaker(cluster_type=clustering.ClusterMaker.FLAT)
    clusters, models = clusterer.cluster_articles(models, inv_index, threshold=0.40, cluster_method=clustering.ClusterMaker.SNG_LNK)
    for cluster in clusters.values():
        if cluster.db_save():
            print "Cluster " + cluster.get_description() + " saved sucessfully"
        else:
            print "Cluster " + cluster.get_description() + " NOT saved sucessfully"
    t2 = time.time()
    '''
    evaluator = Evaluator()
    print "Rand Index: " + str(evaluator.rand_index(clusters, models))
    print "        TP: " + str(evaluator.totaltruepos)
    print "        TN: " + str(evaluator.totaltrueneg)
    print "        FP: " + str(evaluator.totalfalsepos)
    print "        FN: " + str(evaluator.totalfalseneg)
    print "F-measure:  " + str(evaluator.f_measure(3))
    print "Purity:     " + str(evaluator.purity(clusters, models))
    print "NMI:        " + str(evaluator.nmi(clusters, models))'''
    print str(t2 - t1)