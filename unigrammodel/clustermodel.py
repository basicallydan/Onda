'''
Created on 20 Feb 2010

@author: Dan
'''

import time

import MySQLdb
import MySQLdb.cursors
from retrieval import article
from auxfunctions import chunks
from auxfunctions import database
import clusterloader
import cosinecomparer
import threading
import articleunigram
from unigrammodel.cosinecomparer import CosineComparer

class ClusterModel(object):
    """
    Represents a cluster of articles. Includes the group average model of all
    the articles as an article model.
    """
    
    GRP_AVG = 0
    SNG_LNK = 1
    CMP_LNK = 2
    cluster_methods = {GRP_AVG: "Group Average", SNG_LNK: "Single Link", CMP_LNK: "Complete Link"}
    
    def __init__(self, inv_index=None, seed_article=None, cluster_method=SNG_LNK, freq_class_id=None, save_to_db=False, id=None, load_full_article=True):
        """
        Creates a new cluster, usually from a seed article but could be one
        loaded from the database
        """
        self.inv_index = inv_index
        self.description = None
        self.top_article = None
        self.load_full_article = load_full_article
        if cluster_method in self.cluster_methods.keys():
            self.cluster_method = cluster_method
        else:
            print "Clustering method not found, defaulting to single link"
            self.cluster_method = self.SNG_LNK
        if seed_article:
            # top_article is at first the seed article with a 50% similarity
            self.top_article = (seed_article, 0)
            self.articles = [seed_article]
            self.model = seed_article.copy()
            self.id = None
            if freq_class_id:
                self.set_freq_class(freq_class_id)
            if save_to_db:
                self.db_create_row()
        elif id:
            self.db_load(id)
        self.edited = False

    def __str__(self):
        return "Cluster " + str(self.id) + ", top article: " + str(self.get_top_article().article)
    
    def __iter__(self):
        return self.articles.__iter__()
    
    def __len__(self):
        return len(self.articles)

    def get_top_article(self):
        return self.top_article[0]

    def delete(self,db,new_id = None):
        """
        Clusters are never fully deleted, only they given a 'new cluster' ID
        when they are merged with that cluster. THis is used to redirect to the
        new cluster
        """
        cur = db.cursor()
        term_delete_query = "DELETE FROM cluster_terms WHERE `clusterid` = %d" % (self.id)
        cur.execute(term_delete_query)
        if new_id:
            cluster_update_query = "UPDATE clusters SET `newclusterid` = %d WHERE `id` = %d" % (new_id,self.id)
            cur.execute(cluster_update_query)
        cur.close()
        db.commit()

    def db_load(self, id, db=None):
        close_db = False
        if not db:
            close_db = True
            db = database.connect_to_database()
        query = "SELECT * FROM clusters WHERE `id` = %d" % (id)
        print query
        cur = db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        cur.execute(query)
        result = cur.fetchone()
        print result
        self.from_db_values(result)
        cur.close()
        self.db_load_articles(db)
        if close_db:
            db.close()

    def db_load_articles(self, top_article_id, db=None):
        """ Loads all the ArticleModel instances relating to this cluster """
        article_list = article.db_get_all_articles("`clusterid` = %d" % self.id)
        models,inv_index = articleunigram.db_load_models(article_list)
        self.articles = models.values()

        close_db = False
        if not db:
            close_db = True
            db = database.connect_to_database()
        cur = db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        terms_query = "SELECT `term`,`tf`,`count` FROM clusterswithterms WHERE `clusterid` = %d" % (self.id)
        # print str(threading.currentThread().getName()) + ": Going to load cluster model term from DB with query " + terms_query
        num_rows = cur.execute(terms_query)
        db_rows = cur.fetchall()
        # print str(threading.currentThread().getName()) + ": Loading terms for cluster " + str(self.id) + ": " + str(num_rows) + " rows..."
        self.model = articleunigram.ArticleModel()
        self.model.from_db_values(db_rows)
        cur.close()
        if close_db:
            db.close()
        # self.top_article = models[top_article_id]

    def from_db_values(self, db_values, load_model=True):
        """ Given a dictionary of values from the DB, load this cluster """
        print db_values
        self.id = db_values['id']
        self.description = db_values['description']
        if load_model:
            self.db_load_articles(top_article_id = db_values['toparticleid'])
        self.db_load_top_article(db_values['toparticleid'])

    def db_load_top_article(self,toparticleid,inv_index=None):
        """ Loads the top article of the cluster from the DB """
        # print str(threading.currentThread().getName()) + ": Loading top article..."

        if not self.inv_index:
            self.inv_index = inv_index

        db = database.connect_to_database()
        cur = db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        article_query = "SELECT * FROM articleswithterms WHERE `clusterid` = %d AND `articleid` = %d" % (int(self.id), int(toparticleid))
        # print "Query is " + article_query
        cur.execute(article_query)
        db_values = cur.fetchall()
        article_model = articleunigram.ArticleModel()
        article_model.from_db_values(db_values)
        # print "TOP ARTICLE: " + str(article_model.article)
        comp = cosinecomparer.CosineComparer(self.inv_index)
        self.top_article = (article_model, self.similarity(comp, article_model, self.GRP_AVG))

    def get_description(self):
        """
        Get the determined description of the cluster based on the top article
        """
        if self.description:
            return str(self.description)
        elif str(self.top_article[0]):
            return str(self.top_article[0])
        else:
            return "No desc, cluster " + str(self.id)
    
    def set_of_articles(self):
        """ Instead of a dictionary returns a set of articles ids """
        article_set = set([a_mod.article.id for a_mod in self.articles])
        return article_set

    def set_freq_class(self, id):
        """
        For evaluation purposes, the 'frequent class' is to be set, i.e.
        the gold-standard class which appears most in the cluster
        """
        self.freq_class_id = id

    def set_cluster_method(self, cluster_method):
        """ Set the method by which the cluster is made """
        if cluster_method in self.cluster_methods.keys():
            self.cluster_method = cluster_method
            
    def similarity(self, comp, mod_1, cluster_method):
        """
        Recursive algorithm which compares an article to the cluster, or two
        clusters to one another. If the type is a cluster, the
        compare_to_cluster method used instead.
        """
        if type(self) == type(mod_1):
            return self.compare_to_cluster(comp, mod_1, cluster_method)
        if cluster_method == self.GRP_AVG:
            return comp.similarity(mod_1, self.model)
        elif cluster_method == self.SNG_LNK:
            similarities = [comp.similarity(mod_1, mod_2) for mod_2 in self.articles]
            return max(similarities)
        elif cluster_method == self.CMP_LNK:
            similarities = [comp.similarity(mod_1, mod_2) for mod_2 in self.articles]
            return min(similarities)
    
    def compare_to_cluster(self, comp, clu_1, cluster_method):
        """
        Compares a cluster to a cluster.
        For Group Average, uses the cluster centroids and compares them, but
        otherwise...
        
        For each article in the cluster, get the similarities and return either
        the maximum or the minimum and the associaated article.
        """
        if cluster_method == self.GRP_AVG:
            return comp.similarity(clu_1.model, self.model)
        elif cluster_method == self.SNG_LNK:
            similarities = [self.similarity(comp, mod_1) for mod_1 in clu_1.articles]
            return max(similarities)
        elif cluster_method == self.CMP_LNK:
            similarities = [self.similarity(comp, mod_1) for mod_1 in clu_1.articles]
            return min(similarities)

    def merge(self, cluster):
        """
        Merges two clusters together.
        """
        for article in cluster.articles:
            self.add_article(article, None, None)
        return self

    def db_create_row(self, db=None):
        if not db:
            db = database.connect_to_database()
        description = str(database.db_escape(self.top_article[0].article.title))
        if not description or description == "NULL":
            description = "'None'"
        query = "INSERT INTO clusters (`description`,`toparticleid`) VALUES(%s,%d)" % (description,self.top_article[0].article.id)
        cur = db.cursor()
        cur.execute(query)
        self.id = cur.lastrowid
        db.commit()
        cur.close()

    def reevaluate_centroid(self):
        new_model = articleunigram.ArticleModel()
        for a_mod in self.articles:
            new_model.average_with(a_mod.terms)
        print "NEW:\n" + str(new_model) + "\ncompared to\n"
        print "OLD:\n" + str(self.model) + "\ncompared to\n"


    def db_save(self, db=None, suppress_save = False):
        """
        Makes a number of queries.
        
        1. First of all, sets the description and top article ID of the cluster.
        2. Updates all the articles to have this cluster ID.
        3. Update the cluster terms by looking for the terms in the articles
           and making an average of the counts and frequencies.
        Then,
        """
        # First make sure that saving is required. If no articles have been added to this cluster,
        # then it does not need to be saved.
        if not self.edited:
            return True,"Not Edited"
        try:
            if not db:
                db = database.connect_to_database()
            cur = db.cursor()

            if self.id:
                cluster_up_query = "UPDATE clusters SET `description` = %s,`toparticleid` = %d WHERE `id` = %d" % (database.db_escape(self.top_article[0].article.title),self.top_article[0].article.id, self.id)
            else:
                self.db_create_row(db)

            # now we update the articles with their clusters
            # queries = [str(a_mod.get_cluster_update_query()) for a_mod in self.articles]
            # article_up_query = ";".join(queries)
            article_up_query = "UPDATE articles SET clusterid = %d WHERE id IN (%s)" % (self.id,",".join([str(a_mod.article.id) for a_mod in self.articles]))
            print "Running query " + article_up_query + " to update the articles in cluster " + str(self.id)

            success = True
            for term in self.model.terms:
                message = "Success!"
                # first get the stem id of the term
                query = "SELECT `id` FROM unigram_stems WHERE `term` = %s" % (database.db_escape(term))
                cur.execute(query)
                result = cur.fetchone()
                term_id = result[0]
                tf = self.model.terms[term][0]
                count = int(self.model.terms[term][1])
                # first check for the existence of the link
                #query = "SELECT `clusterid` FROM cluster_terms WHERE `stemid` = %d AND clusterid = %d" % (term_id,self.id)
                #print query
                #cur.execute(query)
                #result = cur.fetchone()
                #if not result:
                    # Make the link table row
                query = "INSERT INTO cluster_terms (`stemid`,`clusterid`,`count`,`tf`) VALUES(%d,%d,%d,%.3f) ON DUPLICATE KEY UPDATE `count` = VALUES(`count`),`tf` = VALUES(`tf`)" % (term_id, self.id, count, tf)
                # print query
                #else:
                #    query = "UPDATE cluster_terms SET `count` = %d, `tf` = %.3f WHERE `stemid` = %d AND %clusterid = %d" % (count,tf,term_id,self.id)
                cur.execute(query)
            cur.execute(article_up_query)
            cur.close()
            cur = db.cursor()

            if cluster_up_query:
                cur.execute(cluster_up_query)
                cur.close()
        except MySQLdb.Error, e:
            message = "Error %d: %s" % (e.args[0], e.args[1])
            success = False
        except AttributeError, e:
            message = "Error: Attribute not found: " + str(e)
            success = False
        finally:
            if success and not suppress_save:
                db.commit()
            else:
                db.rollback()
            return success, message
    
    def add_article(self, article_model, sim, comp, inv_index = None):
        """
        Adds an article to the group average model only if GAC is being used
        
        Also adds an article to the list.

        The comparer, inverted index and total counts are needed to determine
        the actual similarity of the seed if its all that exists.
        """

        if not self.inv_index:
            self.inv_index = inv_index

        print "Adding " + str(article_model.article) + " to " + str(self)

        self.model.terms.average_with(article_model.terms)

        if not comp:
            comp = CosineComparer(self.inv_index)

        if not sim:
            sim = self.similarity(comp, article_model, self.cluster_method);

        if len(self.articles) == 1:
            print "Only one article, so the top article is the first one."
            # i.e. only one article, the seed
            self.top_article = (self.articles[0], self.similarity(comp, self.articles[0], self.cluster_method))
        if sim > self.top_article[1]:
            print "The new article, " + str(article_model) +" is more rep. than " + str(self.top_article[0]) + " because " + str(sim) + " > " + str(self.top_article[1])
            self.top_article = (article_model, sim)
        else:
            print "The new article, " + str(article_model) +" is NOT more rep. than " + str(self.top_article[0]) + " because " + str(sim) + " < " + str(self.top_article[1])
        article_model.set_cluster(self.id, False)
        self.articles.append(article_model)
        self.edited = True
    
    def print_articles(self):
        for article_model in self.articles:
            print str(article_model.article)

def get_all_clusters(start_date=None, end_date=None, sql_conds=None, inv_index=None, num_threads=1):
    """ Gets all the clusters given some conditions """
    db = database.connect_to_database()
    query = "SELECT * FROM clusterswitharticles"
    cur = db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    linker = "WHERE"
    if start_date:
        query += " %s `earliest` >= '%s'" % (linker, str(start_date))
        linker = "AND"
    if end_date:
        query += " %s `latest` <= '%s'" % (linker, str(start_date))
        linker = "AND"
    if sql_conds:
        query += " %s %s" % (linker, sql_conds)

    cur.execute(query)
    results = cur.fetchall()
    cur.close()
    db.close()

    chunk_sizes = int(float(len(results)) / float(num_threads))
    cluster_lists = chunks.chunks(results, chunk_sizes)
    print "Loading " + str(len(cluster_lists)) + " cluster lists of size " + str(chunk_sizes) + " using " + str(num_threads) + " threads"
    cluster_loaders = list()
    for c_list in cluster_lists:
        cluster_loaders.append(clusterloader.ClusterLoader(c_list,inv_index))
    for loader in cluster_loaders:
        loader.start()
    # print "Getting as far as starting the threads"
    while threading.activeCount() > 1:
        print "Waiting for " + str(threading.activeCount() - 1) + " threads to finish:\n\t",
        for loader in cluster_loaders:
            print loader.getName() + ": cluster " + loader.get_current_cluster(),
        print "."
        time.sleep(5)
    clusters = dict()
    for loader in cluster_loaders:
        clusters.update(loader.get_clusters())
        loader = None
    cluster_loaders = None
    """
    num_clusters = len(results)
    for row, index in zip(results, xrange(num_clusters)):
        print "Loading cluster " + str(index) + "/" + str(num_clusters)
        new_cl = ClusterModel()
        new_cl.from_db_values(row,inv_index=inv_index)
        clusters[new_cl.id] = new_cl
    """
    return clusters