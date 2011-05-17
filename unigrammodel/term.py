'''
Created on 11 Feb 2010

@author: Daniel Hough
'''
import math

from auxfunctions import PorterStemmer
from auxfunctions import termproc

class InvertedIndex(object):
    def __init__(self):
        self.inv_index = dict()
        self.all_docs = set()

    def __len__(self):
        return len(self.inv_index)
        
    def add_term_ocurrence(self,term,doc_id):
        self.all_docs.add(doc_id)
        if self.inv_index.has_key(term):
            self.inv_index[term].add(doc_id)
        else:
            self.inv_index[term] = set([doc_id])
    
    def add_term_occurences(self,term_list,doc_id):
        for term in term_list:
            self.add_term_ocurrence(term, doc_id)

    def size(self):
        return len(self.inv_index)
    
    def num_docs(self,term):
        if self.inv_index.has_key(term):
            num_of_docs = len(self.inv_index[term])
        else:
            num_of_docs = 1
        # print str(term) + " is found in " + str(num_of_docs) + " docs"
        return num_of_docs
    
    def idf(self,term):
        idf = math.log(float(len(self.all_docs)) / float(self.num_docs(term)))
        return idf

    def terms_as_string_list(self):
        return "'" + str("','".join(self.inv_index.keys())) + "'"

class TermList(object):
    '''
    A dictionary of term and their counts.
    '''

    def __init__(self):
        '''
        This object is an extension of dict
        The key is a stemmed term.o
        However, a dictionary of terms
        and their stems are also stored to reduce processing
        I.e. so the porter stemmer doesn't need to run
        unnecessarily.
        '''
        self.terms_dict = dict()
        self.stem_map = dict()
        self.stemmer = PorterStemmer.PorterStemmer()
    
    def __setitem__(self,term,value):
        '''
        Sets the parts of a term
        '''
        self.terms_dict[term] = value
    
    def __getitem__(self,term):
        '''
        Returns a term as efficiently as possible
        '''
        orig_term = term
        if not self.terms_dict.has_key(orig_term):
            if self.stem_map.has_key(term):
                term = self.stem_map[term]
            else:
                term = self.stemmer.stem(orig_term,0,len(orig_term) - 1)
        if self.terms_dict.has_key(term):
            return self.terms_dict[term]
        else:
            print "Term not found"
    
    def __iter__(self):
        return self.terms_dict.__iter__()
    
    def __contains__(self,key):
        return self.terms_dict.has_key(key)
    
    def __len__(self):
        return len(self.terms_dict)
    
    def all_terms(self):
        return self.terms_dict.keys()
    
    def set_terms(self,term_list):
        self.terms_dict = dict(term_list)
    
    def set_tf(self,term,tf):
        self.terms_dict[term][0] = tf
    
    def set_count(self,term,count):
        self.terms_dict[term][1] = count
    
    def count_term(self,term,denominator = 1, weight = 1):
        '''
        When a term is added it is assumed to be prepared
        except for stemming, i.e. it must be lowercase if
        necessary, and stoplist-checked.
        '''
        term = termproc.conflate(term)
        orig_term = term
        if self.stem_map.has_key(term):
            term = self.stem_map[term]
        else:
            term = self.stemmer.stem(orig_term,0,len(orig_term) - 1)
            self.stem_map[orig_term] = term
        if self.terms_dict.has_key(term):
            self.terms_dict[term][0] += (float(1) * weight) / denominator
            self.terms_dict[term][1] += 1
            self.terms_dict[term][2].add(orig_term)
        else:
            self.terms_dict[term] = [(float(1) * weight) / denominator,1,set([orig_term])]
        return term
    
    def add_term(self,term,count,orig_terms = None):
        '''
        Adds a term with a count, and increments the values for the term in this
        model if it already exists -i.e. gets an average
        '''
        if self.terms_dict.has_key(term):
            self.terms_dict[term][0] = ((self.terms_dict[term][0] * self.terms_dict[term][1]) + count) / self.terms_dict[term][0] + 2
            self.terms_dict[term][1] += 1
            self.terms_dict[term] = (((self.terms_dict[term][0] * self.terms_dict[term][1]) + count) / self.terms_dict[term][0] + 2)
    
    def average_with(self,other_term_list):
        other_terms_dict = other_term_list.terms_dict
        new_term_dict = dict()
        term_set = set(other_terms_dict.keys()).union(set(self.terms_dict.keys()))
        for term in term_set:
            if self.terms_dict.has_key(term):
                tf_1 = self.terms_dict[term][0]
                count_1 = self.terms_dict[term][1]
                if self.terms_dict[term][2]: # i.e., are there any original terms?
                    orig_terms_1 = self.terms_dict[term][2]
                else:
                    orig_terms_1 = set()
            else:
                tf_1 = 0.0
                count_1 = 0
                orig_terms_1 = set()
            if other_terms_dict.has_key(term):
                tf_2 = other_terms_dict[term][0]
                count_2 = other_terms_dict[term][1]
                if other_terms_dict[term][2]: # i.e., are there any original terms?
                    orig_terms_2 = other_terms_dict[term][2]
                else:
                    orig_terms_2 = set()
            else:
                tf_2 = 0.0
                count_2 = 0
                orig_terms_2 = set()
            # finally make the new term:
            new_term_dict[term] = (((tf_1 * count_1) + count_2) / (tf_1 + 2),count_1 + count_2,orig_terms_1.union(orig_terms_2))
        self.terms_dict = new_term_dict
    
    def print_terms(self):
        for term in self.terms_dict.items():
            print term[0] + " => " + str(term[1][0]) + " (" + ",".join(term[1][2]) + ")"