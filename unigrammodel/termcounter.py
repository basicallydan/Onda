# To change this template, choose Tools | Templates
# and open the template in the editor.
from auxfunctions import database
from term import InvertedIndex
from threading import Thread
from articleunigram import ArticleModel
__author__="Dan"
__date__ ="$16-Mar-2010 22:53:42$"
class TermCounter(Thread):
    def __init__(self, articles, store=True,title_weight=19, print_steps=False, leading_weight=1,stoplist_file="../stop_words"):
        """A termcounter, which counts terms in a separate thread"""
        Thread.__init__(self)
        self.articles = articles
        self.store = store
        self.title_weight = title_weight
        self.print_steps = print_steps
        self.leading_weight = leading_weight
        self.stoplist_file = stoplist_file
    def run(self):
        if self.store:
            db = database.connect_to_database()
        models = dict()
        inv_index = InvertedIndex()
        num_articles = len(self.articles)
        for art, index in zip(self.articles, xrange(len(self.articles))):
            if self.print_steps:
                print str(self.getName()) + ": Counting terms of article " + str(index + 1) + "/" + str(num_articles)
            model = ArticleModel(art, self.title_weight, self.leading_weight, stoplist_file = self.stoplist_file)
            for term in model.count_terms():
                inv_index.add_term_ocurrence(term, model.article.id)
            if self.store:
                model.db_save(db)
            models[art.id] = model
        """ This isn't needed anymore
        total_counts = sum([model.total_term_counts for model in models.values()])
        if self.store:
            cur = db.cursor()
            query = "UPDATE terms_global SET totaltermcounts = totaltermcounts + %d WHERE id = 1" % (total_counts)
            cur.execute(query)
        """
        return models, inv_index