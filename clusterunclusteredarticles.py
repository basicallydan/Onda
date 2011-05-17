import threading
import time
#! /usr/bin/python

# To change this template, choose Tools | Templates
# and open the template in the editor.

from unigrammodel import clustering
from unigrammodel import clustermodel
from unigrammodel import articleunigram
import datetime
import time
import threading
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

    # article_list = article.db_get_all_articles("isnull(clusterid) AND counted = 1")
    article_list = article.db_get_all_articles("isnull(clusterid) AND EXISTS (SELECT articleid FROM articleswithterms WHERE articleid = articles.id) AND `datepublished` >= '%(weekago)s'" % {"weekago" : week_ago_date_mysql})
    if len(article_list) > 0:
        models,inv_index = articleunigram.db_load_models(article_list)
        relevant_terms = inv_index.terms_as_string_list()
        existing_clusters = clustermodel.get_all_clusters(sql_conds = "EXISTS (SELECT * FROM clusterswithterms WHERE `term` IN (%(rel)s) AND clusterswithterms.clusterid = clusterswitharticles.id) AND isnull(newclusterid) AND `latest` > '%(daysago)s' OR (`latest` > '%(weekago)s' AND `count` > 2) OR (`count` > 3 AND `latest` < '%(weekago)s' AND `count` < 12) ORDER BY `count` ASC" % {"rel" : relevant_terms,"weekago" : week_ago_date_mysql,"daysago" : days_ago_date_mysql},inv_index = inv_index, num_threads = 1)
        print "Finished loading existing clusters..."
        clusterer = clustering.ClusterMaker(cluster_type=clustering.ClusterMaker.FLAT,existing_clusters = existing_clusters, threshold=0.40, cluster_method=clustermodel.ClusterModel.SNG_LNK,inv_index = inv_index)
        clusters, models = clusterer.cluster_articles(models)
        num_clusters = len(clusters)
        print "Clusters edited, saving..."
        for cluster,index in zip(clusters.values(),xrange(num_clusters)):
            success,message = cluster.db_save()
            print "Saving cluster " + str(index + 1) + "/" + str(num_clusters) + "...",
            if success:
                print "Success! Saved " + str(cluster) + "\n############"
            else:
                print "Fail! Could not save " + str(cluster)
                print str(message) + "\n############"
    else:
        print "No unclustered articles."
    sys.exit(0)