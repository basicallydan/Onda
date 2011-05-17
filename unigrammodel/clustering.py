'''
Created on 20 Feb 2010

@author: Daniel Hough
'''
from cosinecomparer import CosineComparer
from clustermodel import ClusterModel
import operator
from threading import Thread

class ClustererThread(Thread):
    def __init__(self,clusterer,models):
        Thread.__init__(self)
        self.clusterer = clusterer
        self.models = models
        
    def run(self):
        self.clusterer.cluster_articles(self.models)
        

class ClusterMaker(object):
    """
    Takes a set of articles to cluster and some other information
    and clusters them by topic. Also takes existing clusters in case they might
    be relevant.
    """
    FLAT = 0
    AGGL = 1
    cluster_types = {FLAT : "Flat",AGGL : "Agglomerative Hierarchical"}

    def __init__(self,cluster_type = FLAT,existing_clusters = dict(),threshold = 0.40,cluster_method = ClusterModel.SNG_LNK,on_change = None,inv_index = None):
        """
        Constructor.
        """
        self.threshold = threshold
        self.cluster_method = cluster_method
        self.on_change = on_change
        self.comp = CosineComparer(inv_index)
        self.inv_index = inv_index
        
        self.existing_clusters = existing_clusters
        if cluster_type in self.cluster_types.keys():
            self.cluster_type = cluster_type
        else:
            print "Clustering method not found, defaulting to FLAT"
            self.cluster_type = self.FLAT
    
    def cluster_articles(self,models):
        """
        Depending on the specified cluster type (flat or agglomerative)
        clusters the articles
        """
        if self.cluster_type == self.FLAT:
            return self.flat_clustering(models)
        elif self.cluster_type == self.AGGL:
            return self.agglomerative_clustering(models)

    def flat_clustering(self,models):
        """
        Flat clustering merged articles into existing clusters or makes new
        clusters when it's appropriate with a seed article to start.
        """
        clusters = self.existing_clusters
        for mod in models.values():
            if not mod.article.title:
                print "No title for model " + str(mod)
            if len(clusters) == 0:
                # print "Creating first clusters from article with TC " + str(cluster_key) + ": " + mod.article.title
                new_cluster = ClusterModel(self.inv_index,mod,cluster_method = self.cluster_method,save_to_db=True)
                new_cluster.set_freq_class(mod.article.classification)
                cluster_key = new_cluster.id
                clusters[cluster_key] = new_cluster
                mod.set_cluster(cluster_key)
                if self.on_change:
                    self.on_change(clusters=clusters,new_cluster = cluster_key,remove_model = mod.article.title)
                # models.remove(mod)
            else:
                # choose all the candidate clusters, i.e. those which have a
                # similarity greater than or equal to the similarity threshold
                candidate_clusters = []
                for cluster in clusters.items():
                    sim = cluster[1].similarity(self.comp,mod,self.cluster_method)
                    if sim >= self.threshold:
                        candidate_clusters.append((cluster[0],sim))
                        # print "Adding a candidate cluster based on article " + str(cluster[0]) + " for article " + mod.article.title
                if len(candidate_clusters) == 0:
                    # There are no clusters equal to or above the similarity
                    # threshold, so make a new one
                    new_cluster = ClusterModel(self.inv_index,mod,cluster_method = self.cluster_method,save_to_db=True)
                    new_cluster.set_freq_class(mod.article.classification)
                    cluster_key = new_cluster.id
                    clusters[cluster_key] = new_cluster
                    mod.set_cluster(cluster_key)
                    print "Creating a cluster with ID " + str(cluster_key) + " using article " + mod.article.title
                    if self.on_change:
                        self.on_change(clusters = clusters,new_cluster = cluster_key,remove_model = mod.article.title)
                else:
                    # Sort all the candidate clusters by similarity and choose the best one
                    top_clusters = sorted(candidate_clusters,key=operator.itemgetter(1))
                    # print "Article " + mod.article.title + " has " + str(len(top_clusters)) + " candidate clusters"
                    # print "Adding article " + mod.article.title + " to cluster  " + str(top_clusters[0][0]) + " with similarity score " + str(top_clusters[0][1])
                    clusters[top_clusters[0][0]].add_article(mod,top_clusters[0][1],self.comp)
                    mod.set_cluster(top_clusters[0][0])
        return clusters,models
    
    def agglomerative_clustering(self,models):
        """
        Each article is a cluster to start with, and the two most similar
        clusters are merged until no cluster similarities are above the
        threshold.
        """
        clusters = dict([(model.article.id,ClusterModel(self.inv_index,model,cluster_method=self.cluster_method,freq_class_id=model.article.classification)) for model in models.values()])
        best_similarity = 1
        while best_similarity > self.threshold:
            most_similar = []
            for cl_1,index in zip(clusters,xrange(len(clusters))):
                for cl_2 in clusters:
                    if cl_1 != cl_2:
                        sim = clusters[cl_1].similarity(self.comp,clusters[cl_2])
                        if sim >= self.threshold:
                            most_similar.append((cl_1,cl_2,sim))
            if len(most_similar) > 0:
                most_similar = sorted(most_similar,key=operator.itemgetter(2))
                most_similar.reverse()
                sim_pair = most_similar[0]
                '''
                print "Merging " + str(sim_pair[0]) + " and " \
                    + str(sim_pair[1]) \
                    + " with similarity " + str(sim_pair[2])
                '''
                clusters[sim_pair[0]].merge(clusters[sim_pair[1]])
                if sim_pair[2] == 1.0:
                    clusters[sim_pair[0]].print_articles()
                clusters.pop(sim_pair[1])
                best_similarity = sim_pair[2]
                if self.on_change:
                    self.on_change(clusters=clusters)
            else:
                break
            # yield clusters,models
        return clusters,models

    def merge(self,cluster1,cluster2):
        """
        Merges two clusters by adding all the articles from one to the other
        """
        for article in cluster2.articles:
            cluster1.add_article(article,None,self.comp)
        return cluster1