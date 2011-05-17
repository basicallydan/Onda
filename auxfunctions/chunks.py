# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__ = "Dan"
__date__ = "$01-Apr-2010 12:03:30$"

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    if(len(l) < n or n == 0):
        return [l]
    else:
        l_chunks = list()
        for i in xrange(0, len(l), n):
            l_chunks.append(l[i:i + n])
        return l_chunks