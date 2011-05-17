# To change this template, choose Tools | Templates
# and open the template in the editor.

from auxfunctions import database
from retrieval import source
from unigrammodel import clustermodel

__author__ = "Daniel Hough"
__date__ = "$01-Mar-2010 12:55:02$"

class DiversityMeasurer(object):
    def __init__(self,all_clusters):
        self.all_clusters = all_clusters

    def proportion_of_topics_covered(self,source,start_date=None,end_date=None,db=None):
        if not db:
            db = database.connect_to_database()
        total_topics = len(self.all_clusters)
        articles_from_source = source.db_load_articles(start_date, end_date)
        clusters_of_source = set([article.cluster_id for article in source.article_list])
        num_clusters_by_source = len(clusters_of_source)
        return float(num_clusters_by_source) / float(total_topics)


if __name__ == "__main__":
    sources = source.get_all_sources()
    clusters = clustermodel.get_all_clusters(start_date = "2010-01-24", end_date = "2010-01-31")
    measurer = DiversityMeasurer(clusters)
    for source in sources:
        print str(source.newspaper_name) + ": " + str(measurer.proportion_of_topics_covered(source,start_date = "2010-01-24", end_date = "2010-01-31"))