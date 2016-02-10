'''
Created on 25 Feb 2010

@author: Dan
'''

import operator
import math
from auxfunctions import database

class Evaluator(object):
    '''
    This object takes models and clusters, where at least some of the models
    are assumed to have a 'classification' attribute so they can be evaluated
    for accuracy
    '''
    
    def purity(self,clusters,models,print_steps = True):
        self.n = 0.0
        total_correct = 0
        for cluster in clusters.values():
            cluster.set_freq_class(self.most_frequent_class(cluster))
            if cluster.freq_class_id != 0:
                correct = 0
                incorrect = 0
                for a_mod in cluster:
                    if a_mod.article.classification != 0:
                        self.n += 1
                        if a_mod.article.classification == cluster.freq_class_id:
                            correct += 1
                        else:
                            incorrect += 1
                total_correct += correct
        self.purity_measure = float(total_correct) / float(self.n)
        return self.purity_measure
    
    def most_frequent_class(self,cluster):
        classes = dict()
        for a_mod in cluster:
            if a_mod.article.classification:
                if classes.has_key(a_mod.article.classification):
                    classes[a_mod.article.classification] += 1
                else:
                    classes[a_mod.article.classification] = 1
        if len(classes) > 0:
            return max(classes.iteritems(),key = operator.itemgetter(1))[0]
        else:
            return 0
    
    def nmi(self,clusters,models):
        '''
        Normalized Mutural Information
        This is a measure allowing us to make a tradeoff between the quality of
        the clustering against the number of clusters
        '''
        classes = self.get_all_classes(models)
        self.nmi_val = float(self.mutual_information(clusters,models,classes)) / (float(self.entropy(clusters)) + float(self.entropy(classes)) / 2)
        return self.nmi_val
    
    def get_all_classes(self,models):
        classes = dict()
        for a_mod in models.values():
            if classes.has_key(a_mod.article.classification):
                classes[a_mod.article.classification].add(a_mod.article.classification)
            else:
                classes[a_mod.article.classification] = set([a_mod.article.classification])
        return classes
        
    def mutual_information(self,clusters,models,classes):
        result = 0.0
        for cluster in clusters.values():
            for classification in classes.values():
                cluster_size = float(len(cluster))
                class_size = float(len(classification))
                prob_inter = float(len(classification.intersection(cluster.set_of_articles())))
                if prob_inter > 0:
                    result += (prob_inter / self.n) * math.log((self.n * prob_inter) / (cluster_size * class_size))
        return result
                
    
    def entropy(self,cls):
        '''
        Takes either a dict of classes or clusters
        '''
        vals_to_sum = [(float(len(cl)) / self.n) for cl in cls.values()]
        vals_to_sum = [i * math.log(i) for i in vals_to_sum]
        return -sum(vals_to_sum)
    
    def rand_index(self,clusters,models,print_steps = False):
        self.totalcorrect = 0
        self.totalincorrect = 0
        self.totaltruepos = 0
        self.totalfalsepos = 0
        self.totaltrueneg = 0
        self.totalfalseneg = 0
        self.total = 0
        
        self.num_models = len(models)
        self.num_clusters = len(clusters)
        for cluster,index in zip(clusters.items(),xrange(self.num_clusters)):
            if print_steps:
                print "Evaluating cluster " + str(index) + "/" + str(self.num_clusters)
            true_pos = 0
            true_neg = 0
            false_pos = 0
            false_neg = 0
            if print_steps:
                print " Cluster with ID " + str(cluster[0])
            for a_mod_1 in cluster[1].articles:
                if a_mod_1.article.classification != 0:
                    for a_mod_2 in models.values():
                        if a_mod_2.article.classification != 0:
                            if a_mod_1 != a_mod_2:
                                if a_mod_1.cluster_id == a_mod_2.cluster_id:
                                    if a_mod_1.article.classification == a_mod_2.article.classification:
                                        true_pos += 1
                                    else:
                                        false_pos += 1
                                else:
                                    if a_mod_1.article.classification == a_mod_2.article.classification:
                                        false_neg += 1
                                    else:
                                        true_neg += 1
                            #print "  " + article_model.article.title
            correct = true_pos + true_neg
            incorrect = false_pos + false_neg
            total = correct + incorrect
            
            if print_steps:
                print " == Confusion Matrix  =="
                print "          Predicted"
                print "          T     F"
                print " Act| T   %d    %d" % (true_pos,false_neg)
                print " ual| F   %d    %d" % (false_pos,true_neg)
                print "   Correct:   " + str(correct) + "/" + str(total)
                print "   Incorrect: " + str(incorrect) + "/" + str(total)
            self.totalcorrect += correct
            self.totalincorrect += incorrect
            self.totaltruepos += true_pos
            self.totalfalsepos += false_pos
            self.totaltrueneg += true_neg
            self.totalfalseneg += false_neg
        self.total = self.totalcorrect + self.totalincorrect
        self.rand = float(self.totalcorrect) / float(self.total)
        return self.rand
    
    def f_measure(self,b_val = 1.0):
        '''
        Select a b-val > 1 to penalize false negatives more than false positives
        '''
        p = float(self.totaltruepos) / (float(self.totaltruepos) + float(self.totalfalsepos))
        r = float(self.totaltruepos) / (float(self.totaltruepos) + float(self.totalfalseneg))
        b_val_sq = math.pow(b_val,2)
        num = (float(b_val_sq) + 1) * p * r
        den = (float(b_val_sq) * p) + r
        self.fmeasure = float(num) / float(den)
        return self.fmeasure
    
    def print_confusion_matrix(self):
        if self.totaltruepos and self.totalfalsepos and self.totalfalseneg and self.totaltrueneg:
            print "==== REPORT: ===="
            print " Number of articles: " + str(self.num_models)
            print " Number of clusters: " + str(self.num_clusters)
            print "==== FINAL RESULTS ===="
            print "== Final Confusion Matrix  =="
            print "         Predicted"
            print "         T     F"
            print "Act| T   %d    %d" % (self.totaltruepos,self.totalfalseneg)
            print "ual| F   %d    %d" % (self.totalfalsepos,self.totaltrueneg)
            print "\n========\n"
            print " Correct:            " + str(self.totalcorrect) + "/" + str(self.total)
            print " Incorrect:          " + str(self.totalincorrect) + "/" + str(self.total)
            print " Rand Index:         " + str(100 * self.totalcorrect / self.total) + "%"
        else:
            print "You haven't performed a Rand index evaluation"
            
    def db_save(self,thresh,t_weight,l_weight,cl_type,cl_method,timeelapsed):
        db = database.connect_to_database()
        cur = db.cursor()
        query = "INSERT INTO clusterresults (`threshold`,`titleweight`, \
                                             `clustermethod`,`leadingweight`, \
                                             `clustertype`,`truepos`, \
                                             `trueneg`,`falsepos`, \
                                             `falseneg`,`fmeasure`, \
                                             `purity`,`nmi`,`timeelapsed`,\
                                             `rand`) \
                                             VALUES(%.3f,%d,\
                                             '%s',%d,\
                                             '%s',%d,\
                                             %d,%d,\
                                             %d,%.4f,\
                                             %.4f,%.4f,%.4f,\
                                             %.4f)" % \
                                             (thresh,t_weight,cl_method,l_weight,cl_type,\
                                              self.totaltruepos,self.totaltrueneg,\
                                              self.totalfalsepos,self.totalfalseneg,\
                                              self.fmeasure,self.purity_measure,self.nmi_val, \
                                              timeelapsed,self.rand)
        print query
        cur.execute(query)
        db.commit()
        cur.close()