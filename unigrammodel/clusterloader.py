# To change this template, choose Tools | Templates
# and open the template in the editor.
from threading import Thread
import clustermodel
__author__="Dan"
__date__ ="$16-Mar-2010 22:53:42$"
class ClusterLoader(Thread):
    def __init__(self, cluster_list,inv_index):
        Thread.__init__(self)
        self.cluster_list = cluster_list
        self.clusters = dict()
        self.inv_index = inv_index
        self.current_cluster = None
        self.total_clusters = None
    def get_clusters(self):
        return self.clusters
    def get_current_cluster(self):
        return str(self.current_cluster) + "/" + str(self.total_clusters)
    def run(self):
        num_clusters = len(self.cluster_list)
        self.total_clusters = num_clusters
        for row, index in zip(self.cluster_list, xrange(num_clusters)):
            self.current_cluster = index
            new_cl = clustermodel.ClusterModel(self.inv_index)
            new_cl.from_db_values(row)
            self.clusters[new_cl.id] = new_cl
            print "Loaded " + self.get_current_cluster() + "..." + str(new_cl)