'''
Created on 16 Feb 2010

@author: Daniel Hough
'''
    
def conflate(term):
    term_conflated = term.lower()
    term_conflated = term_conflated.replace("'","")
    return term_conflated

def replace_html_chars(term):
    '''
    Replace nbsp, ldquo and rdquo, lsquo and rsquo, as well as amp with their respective characters
    '''
    term = term.replace("&nbsp;"," ")
    term = term.replace("&quot;","\"")
    term = term.replace("&lt;","<")
    term = term.replace("&gt;",">")
    term = term.replace("&ndash;","-")
    term = term.replace("&ldquo;","\"")
    term = term.replace("&rdquo;","\"")
    term = term.replace("&lsquo;","'")
    term = term.replace("&rsquo;","'")
    term = term.replace("&amp;","&")
    term = term.replace("&pound;","GBP ")
    return term