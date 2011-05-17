from retrieval import article
from unigrammodel import termcounter
from auxfunctions import chunks
import time

__author__="Dan"
__date__ ="$16-Mar-2010 21:36:23$"

def start_counting_with_threads(article_list, store=True, title_weight=19, print_steps=True, leading_weight=1, stoplist_file="stop_words", num_threads=1):
    chunk_sizes = int(float(len(article_list)) / float(num_threads))
    article_lists = chunks.chunks(article_list,chunk_sizes)
    print "Counting " + str(len(article_lists)) + " article lists of size " + str(chunk_sizes) + " using " + str(num_threads) + " threads"
    term_counters = list()
    for a_list in article_lists:
        term_counters.append(termcounter.TermCounter(a_list,store,title_weight,print_steps,leading_weight,stoplist_file))
    return term_counters

if __name__ == "__main__":
    # test_parameters()
    t1 = time.time()
    article_list = article.db_get_all_articles("NOT EXISTS (SELECT articleid FROM articleswithterms WHERE articleid = articles.id)")
    # models,inv_index = db_load_models(man_articles)
    # models, inv_index = articleunigram.count_terms_and_store(article_list, store=True, title_weight=19, print_steps=True,stoplist_file="stop_words")
    term_counters = start_counting_with_threads(article_list, store=True, title_weight=19, print_steps=True,stoplist_file="stop_words",num_threads=4)
    for counter in term_counters:
        counter.start()
    """
    print "Counted " + str(len(models)) + " articles, took",
    t2 = time.time()
    print str(t2 - t1) + " seconds."
    """