'''
Created on 20 Feb 2010

@author: Dan
'''
from auxfunctions import termproc
import os

class Stoplist(set):
    '''
    Basically a list of words which shouldn't be counted because they
    are common as muck.
    '''
    def __init__(self,stoplist_path):
        if stoplist_path != None and os.path.isfile(stoplist_path):
            stoplist_file = open(stoplist_path,'r')
            for word in stoplist_file:
                word = str(word).strip()
                self.add(word)
            stoplist_file.close()
        else:
            print "Stoplist file " + stoplist_path + " not found"
    
    def apply(self,term_list):
        new_term_list = list()
        for term in term_list:
            term_conflated = termproc.conflate(term)
            if term_conflated not in self:
                new_term_list.append(term)
        return new_term_list