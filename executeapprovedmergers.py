#! /usr/bin/python

# To change this template, choose Tools | Templates
# and open the template in the editor.

from unigrammodel.clustering import ClusterMaker
from unigrammodel import clustering
from unigrammodel import clustermodel
from unigrammodel import articleunigram
from auxfunctions import database
import datetime
import time
import sys
import MySQLdb
import MySQLdb.cursors
from retrieval import article
import sys

__author__="Dan"
__date__ ="$16-Mar-2010 21:40:24$"

if __name__ == "__main__":
    todays_date = datetime.datetime.today()
    two_week_difference = datetime.timedelta(days=-14)
    week_difference = datetime.timedelta(days=-7)
    two_day_difference = datetime.timedelta(days=-3)
    week_ago_date_mysql = (todays_date + week_difference).strftime("%Y-%m-%d")
    days_ago_date_mysql = (todays_date + two_day_difference).strftime("%Y-%m-%d")
    
    article_list = article.db_get_all_articles("NOT isnull(clusterid) AND EXISTS (SELECT articleid FROM articleswithterms WHERE articleid = articles.id) AND `datepublished` >= '%(weekago)s'" % {"weekago" : week_ago_date_mysql})
    models,inv_index = articleunigram.db_load_models(article_list)

    mergers_query = "SELECT * FROM proposedmergers WHERE `approved` = 1"
    db = database.connect_to_database()
    cur = db.cursor(cursorclass = MySQLdb.cursors.DictCursor)
    clusterer = ClusterMaker(inv_index = inv_index)
    cur.execute(mergers_query)
    result = cur.fetchall()
    proposed_mergers = dict()
    for row in result:
        clusters_query = "SELECT `clusterid` FROM proposedmergers_clusters WHERE `mergerid` = %d" % (row['id'])
        cur.execute(clusters_query)
        clusters = cur.fetchall()
        proposed_mergers[row['id']] = [clustermodel.ClusterModel(inv_index = inv_index,id = cl['clusterid'],load_full_article = True) for cl in clusters]

    for p in proposed_mergers.items():
        print str(p[0]) + ": merging " + ",".join([str(cl) for cl in p[1]]) + "..."
        new_cluster = p[1][0]
        clusters_to_merge = p[1][1:]
        print str(new_cluster)
        print str(clusters_to_merge)
        for cl in clusters_to_merge:
            print "Merging " + str(cl) + " into " + str(new_cluster)
            new_cluster = clusterer.merge(new_cluster, cl)
        print "Finished merging, saving..."
        success,message = new_cluster.db_save(db)
        print str(success) + " message: " + str(message)
        if success:
            for cl in clusters_to_merge:
                cl.delete(db,new_cluster.id)
            delete_merger_query = "DELETE FROM proposedmergers WHERE `id` = %d" % (p[0])
            delete_mclusters_query = "DELETE FROM proposedmergers_clusters WHERE `mergerid` = %d" % (p[0])
            cur.execute(delete_merger_query)
            cur.execute(delete_mclusters_query)
        print str(new_cluster)
    sys.exit(0)