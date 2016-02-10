'''
Created on 20 Feb 2010

@author: Daniel Hough
'''

import math

class CosineComparer(object):
    def __init__(self,inv_index):
        self.inv_index = inv_index

    def similarity(self,model_1,model_2):
        potential = False
        for term in model_1.terms:
            if term in model_2.terms:
                potential = True
        if not potential:
            return 0
        numerator = self.dot_product(model_1.terms, model_2.terms)
        denominator = self.magnitude(model_1.terms) * self.magnitude(model_2.terms)
        return (numerator / denominator)
    
    def dot_product(self,vec_1,vec_2):
        dot_prod = 0
        for term in vec_1:
            if term in vec_2:
                # The value stored in vec_1 and vec_2 is the TF, inv_index can make IDF
                dot_prod += (vec_1[term][0] * self.inv_index.idf(term)) * (vec_2[term][0] * self.inv_index.idf(term))
        return dot_prod
    
    def magnitude(self,vec):
        inner = 0
        for term in vec:
            inner += math.pow(vec[term][0] * self.inv_index.idf(term), 2)
        return math.sqrt(inner)