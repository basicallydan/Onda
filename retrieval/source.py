'''
Created on 12 Jan 2010

@author: Daniel Hough
'''

import article
import datetime
import MySQLdb.cursors
import pyrss
from auxfunctions import database
from auxfunctions import termproc

class NewsSource(object):
    '''
    This class represents a news source.
    It is, in other words, the class containing information
    about a newspaper and its website where the RSS feed is coming
    from.
    '''

    def __init__(self,id,db,run_datetime=None,load_articles=False):
        '''
        Takes an ID, which can be used to either load from the database or
        create a new source which can later be saved to the database.
        If a database connection is given, it will attempt to load
        the source information
        '''
        self.id = id
        self.newspaper_name = None
        self.website_name = None
        self.website_url = None
        self.rss_url = None
        self.article_tags = None
        self.description = None
        self.rows_affected = 0
        self.duplicates_found = 0
        self.db = db
        self.article_list = None
        if run_datetime:
            self.run_datettime = run_datetime
        else:
            self.run_datettime = datetime.datetime.now()
        self.db_load_info()
        
        if load_articles:
            print "Loading articles"
            self.article_list = self.db_load_articles()
        
    def get_attrs_and_tags(self,tags_to_find):
        # Assuming "tag_to_find" is a tag followed by either a class name or id
        tags = list()
        for tag_to_find in tags_to_find:
            if "#" in tag_to_find:
                type_of_attr = "id"
                tag_to_find = tag_to_find.split("#")
            else:
                type_of_attr = "class"
                tag_to_find = tag_to_find.split(".")
            tags.append((type_of_attr,tag_to_find[1]))
        return tags
    
    def db_load_info(self):
        try:
            # create a database cursor (emulated by MySQLdb)
            cursor = self.db.cursor()
            # get the source with the ID the same as this one
            cursor.execute("SELECT * FROM sources WHERE id = '" + self.id + "'")
            source_info = cursor.fetchone()
            if cursor.rowcount != 1:
                raise RuntimeError("Could not find the source '" + str(self.id) + "' in the database")
            self.newspaper_name = source_info[1]
            self.website_name = source_info[2]
            self.website_url = source_info[3]
            self.rss_url = source_info[4]
            # used to be only one tag per source
            # self.article_tags = source_info[5]
            self.description = source_info[6]
            cursor.execute("SELECT tag_attribute_value FROM bad_tag_attributes WHERE source_id = '" + self.id + "'")
            self.bad_attribute_values = database.get_first_column(cursor.fetchall())
            cursor.execute("SELECT article_tag FROM target_tags WHERE source_id = '" + self.id + "' ORDER BY `order` ASC")
            self.article_tags = self.get_attrs_and_tags(database.get_first_column(cursor.fetchall()))
            cursor.close()
            self.db.commit()
        except Exception, err:
            print(err)
    
    def db_load_articles(self,start_date = None,end_date = None,sql_conditions = None,force_query = False):
        if force_query or not self.article_list:
            # we need a DictCursor for this one
            cur = self.db.cursor(cursorclass = MySQLdb.cursors.DictCursor)
            query = "SELECT * FROM articles WHERE `source`='" + str(self.id) + "'"
            
            if start_date:
                query += " AND `datepublished` >= '" + str(start_date) + "'"
            if end_date:
                query += " AND `datepublished` <= '" + str(end_date) + "'"
                
            if sql_conditions:
                # so basically sql_conditions needs to be in SQL format - none of that easy-to-use stuff
                # it just complicates things.
                query += " AND " + sql_conditions
            cur.execute(query)
            results = cur.fetchall()
            article_list = [article.Article(db_values = a,source = self) for a in results]
            self.article_list = article_list
            cur.close()
        return self.article_list
            
    def web_download_articles(self):
        '''
        Downloads the latest articles from the RSS feed
        for this source, only taking the ones which have not already been
        taken
        '''
        # set up the database cursor
        cursor = self.db.cursor()
        rss_reader = pyrss.RSSReader(self.rss_url)
        articles_to_add = dict()
        num_candidate_articles = 0
        for rss_item in rss_reader.GetItems():
            if(rss_item):
                # now we run a quick query to see which articles
                # already exist in the database...
                query_for_duplicates = "SELECT guid FROM articles WHERE guid = '" + str(rss_item.guid) + "'"
                cursor.execute(query_for_duplicates)
                existing_articles = database.get_first_column(cursor.fetchall())
                if len(existing_articles) == 0:
                    item_article = article.Article(tag_to_find = self.article_tags,article_rss_item = rss_item,source = self)
                    article_query_values = item_article.get_article_values()
                    if article_query_values:
                        values = "(" + article_query_values + ")"
                        articles_to_add[item_article.guid] = values
                        yield "Adding candidate article " + item_article.title
                        num_candidate_articles += 1
                    else:
                        yield "Ignoring article " + item_article.title
        query_for_duplicates = "SELECT guid FROM articles WHERE guid = '" + "' OR guid = '".join(articles_to_add.keys()) + "'"
        cursor.execute(query_for_duplicates)
        existing_articles = database.get_first_column(cursor.fetchall())
        articles_to_add = [qu[1] for qu in articles_to_add.items() if qu[0] not in existing_articles]
        if articles_to_add:
            query = "INSERT INTO `articles`"\
                " (`guid`, `url`, `source`, `title`, `author`, `originaltext`, `datepublished`, `dateretrieved`) "\
                "VALUES " + ",".join(articles_to_add)
            cursor.execute(query)
            self.rows_affected = cursor.rowcount
            cursor.close()
            self.db.commit()
        else:
            self.rows_affected = 0
        self.duplicates_found = num_candidate_articles - len(articles_to_add)
    
    def web_update_article_text(self):
        '''
        To be used when the article text needs to be re-downloaded for one reason or another.
        '''
        cursor = self.db.cursor()
        num_articles = len(self.article_list)
        current_article = 1
        queries = list()
        if self.article_list:
            for article in self.article_list:
                article.download_article_text()
                article_text = database.db_escape(article.article_text)
                if article_text == None or article_text == "None" or article_text == "NULL":
                    print "Article broken."
                else:
                    cur_query = "UPDATE `articles` SET `originaltext` = \"" + article_text + "\" WHERE `id` = " + str(article.id)
                    queries.append(cur_query)
                print "Source " + str(self.website_name) + " processed " + str(current_article) + "/" + str(num_articles)
                current_article += 1
                if len(queries) >= 5:
                    for query in queries:
                        cursor.execute(query)
                    queries = []
        else:
            print "Article list has not been compiled."
        cursor.close()
        self.db.commit()
        
    def print_info(self):
        print "ID: " + str(self.id)
        print "Website: " + str(self.website_name) + " from " + str(self.newspaper_name)
        print "         (" + str(self.website_url) + ")"
        print "RSS URL: " + str(self.rss_url)
        print "Article tag: " + str(self.article_tags)
        print "Description:\n" + str(self.description)

    def get_all_clusters(self):
        query = "SELECT * FROM clusters"

def get_all_sources():
    db = database.connect_to_database()
    c = db.cursor()
    source_query = "SELECT id FROM sources"
    c.execute(source_query)
    results = c.fetchall()
    sources = [NewsSource(result[0],db) for result in results]
    return sources

def redownload_all_articles():
    all_sources = get_all_sources()
    for source in all_sources:
        source.db_load_articles()
        source.web_update_article_text()

if __name__ == "__main__":
    #run_all_sources()
    redownload_all_articles()

    '''
    dailymail = NewsSource("dailymail",db,now)
    list_of_articles = dailymail.db_load_articles()
    print list_of_articles[0].title
    print list_of_articles[0].article_text
    '''