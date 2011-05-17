from BeautifulSoup import BeautifulSoup
import datetime
import re
import urllib
from urllib2 import urlopen,HTTPError,URLError,Request
import logging
import MySQLdb.cursors
import sys
sys.path.insert(0, '../') 
from auxfunctions.database import db_escape,format_date,connect_to_database

class Article(object):
	def __init__(self, tag_to_find = None, article_rss_item = None, db_values = None, source = None, id = None):
		self.source = source
		# should this article be stored? Default is yes, but
		# depending on what the article contains this might change.
		self.store = True
		
		if article_rss_item:
			# So we're making a new one eh?
			if not tag_to_find:
				# put an exception here
				pass
			if not source:
				# another exception here
				pass
			self.rss_create_new_article(article_rss_item)
			# self.type_of_attr,self.tag_to_find = self.get_attr_and_tags(tag_to_find)
			# download the file contents from the RSS link 
			self.download_article_text()
		elif db_values:
			self.from_db_values(db_values)
		elif id:
			values = self.db_load_article(id)
			self.from_db_values(values)

        def __str__(self):
            return "Article " + str(self.id) + ": " + str(self.title)
			
	def rss_create_new_article(self,rss_item):
		self.original_address = rss_item.link
		self.title = rss_item.title
		self.description = rss_item.description
		self.author = rss_item.author
		self.guid = rss_item.guid
		self.date_published = rss_item.date_published
		self.date_retrieved = datetime.datetime.now()
		self.classification = 0
		
	def from_db_values(self,db_values):
		self.original_address = db_values['url']
		self.title = db_values['title']
		self.author = db_values['author']
		self.guid = db_values['guid']
		self.id = db_values['id']
		self.article_text = db_values['originaltext']
		self.date_published = db_values['datepublished']
		self.date_retrieved = db_values['dateretrieved']
		self.classification = db_values['trainingcluster']
		self.has_been_counted = bool(db_values['counted'])
                self.cluster_id = db_values['clusterid']
	
	def db_load_article(self,id):
		db = connect_to_database()
		cur = db.cursor(cursorclass = MySQLdb.cursors.DictCursor)
		query = "SELECT * FROM articles WHERE `id`='" + str(id) + "'"
		cur.execute(query)
		result = cur.fetchone()
		cur.close()
		return result
	
	def db_set_classification(self,cluster_id):
		self.classification = cluster_id
		db = connect_to_database()
		c = db.cursor()
		query = "UPDATE articles SET trainingcluster = " + str(cluster_id) + " WHERE articles.id = " + str(self.id)
		print "executing " + query
		c.execute(query)
		if db.affected_rows() != 0:
			return True
		else:
			return False
		
	def get_attr_and_tags(self,tag_to_find):
		# Assuming "tag_to_find" is a tag followed by either a class name or id
		if "#" in tag_to_find:
			type_of_attr = "id"
			tag_to_find = tag_to_find.split("#")
		else:
			type_of_attr = "class"
			tag_to_find = tag_to_find.split(".")
		return type_of_attr,tag_to_find
	
	def download_article_text(self):
		file_contents = self.download_page(self.original_address)
		self.article_text = self.extract_article_text(file_contents)

	def download_page(self,remote_file_name):
		download_logger = logging.getLogger('DownloadLogger')
		download_logger.setLevel(logging.ERROR)
                user_agent = 'onda - http://www.danielhough.co.uk/projects/disseration - daniel.hough@gmail.com'
                # Create a request object
                req = Request(remote_file_name)
                req.add_header('User-Agent', user_agent)
		try:
			page = urlopen(req)
			page_contents = page.read()
		except HTTPError:
			download_logger.error("404 not found: " + str(remote_file_name))
			page_contents = None
			pass
		except URLError:
			download_logger.error("Page timed out: " + str(remote_file_name))
			page_contents = None
			pass
		except Exception,e:
			download_logger.error("Unknown error: " + str(e))
			pass
		return page_contents
	
	def extract_article_text(self,entire_page):
		if entire_page == None: return None
		soup = BeautifulSoup(entire_page)
		# let's remove crap we don't want using BeautifulSoup
		# create a list of elements to remove, eventually we'll remove them
		elements_to_remove = []
		for attr_value in self.source.bad_attribute_values:
			for attribute_name in ["class","id"]:
				attr_and_val_to_remove = {attribute_name : attr_value}
				elements_to_remove.extend(soup.findAll(attrs = attr_and_val_to_remove))
		
		# now that the list is complete, remove those suckers
		[element.extract() for element in elements_to_remove]
		
		# now find the source article... it may not exist, if it's been removed because it's
		# inside a bad tag. So it goes.
		article_text_list = []
		for tag in self.source.article_tags:
			attr_and_val_to_find = {tag[0] : tag[1]}
			article_text_list.extend(soup.findAll(attrs = attr_and_val_to_find))
		# article_text_list = soup.findAll(attrs={self.type_of_attr : self.tag_to_find})
		article_text = "\n\n".join([str(p) for p in article_text_list]) 
		
		# create regex patterns for different uses:
		# create_newlines finds all the </p><p> pairs or <br/> tags to replace with a \n
		re_create_newlines = re.compile("(</p>[\s]*<p>|<br />[\s]*<br />|<br>[\s]*<br>|\n[\s]*\n)+?", re.I)
		# re_single_br will replace a single <br> with a space, as its likely
		# that it was used to break up a line (@ the daily maiL!!)
		# or a single newline sometimes splits them up
		re_single_br = re.compile("(<br />|<br>){1}?", re.I)
		# re_javascript removes all tags and the text inside them which are re_javascript tags
		re_javascript = re.compile("(<script.*?>.*?</script>)+?",re.DOTALL)
		# re_all_html removes all HTML that's left after all that, just in case, but NOT the text inside.
		re_all_html = re.compile('<.*?>')
		# it's likely the above regex will result in a LOT of whitespace, so any large blocks of it will
		# be conflated to a single version of whatever it is
		re_spaces = re.compile('[ \t]+')
		re_newlines = re.compile('[\n]+')
		# also some articles may include the title text, and we don't need to see that again
		re_title = re.compile(re.escape(self.title),re.I)
		
		#=======================================================================
		# print self.original_address + ":"
		# print article_text
		#=======================================================================
		# article_text = areas_to_remove.sub('', article_text)
		article_text = re_javascript.sub('', article_text)
		#=======================================================================
		# print "JAVASCRIPT REMOVED:\n",
		# print article_text
		#=======================================================================
		article_text = re_create_newlines.sub('\n', article_text)
		#=======================================================================
		# print "PARAGRAPHS REPLACED:\n",
		# print article_text
		#=======================================================================
		article_text = re_single_br.sub(' ', article_text)
		#=======================================================================
		# print "SINGLE BRS REMOVED:\n",
		# print article_text
		#=======================================================================
		article_text = re_all_html.sub('', article_text)
		#=======================================================================
		# print "HTML REMOVED:\n",
		# print article_text
		#=======================================================================
		article_text = re_newlines.sub('\n', article_text)
		article_text = re_spaces.sub(' ', article_text)
		# only remove the title once
		article_text = re_title.sub('', article_text,count=1)
		#=======================================================================
		# print "WHITEPSACE CONFLATED:\n",
		# print article_text
		#=======================================================================
		return article_text
	
	def get_article_values(self):
		# Gotta filter them values
		article_text = db_escape(self.article_text)
		if article_text == None or article_text == "None" or article_text == "NULL":
			# if it's an empty article just don't bother
			return None
		query = "" + str(db_escape(self.guid)) + "," + str(db_escape(self.original_address)) + "," + str(db_escape(self.source.id)) + \
		  "," + str(db_escape(self.title)) + "," + str(db_escape(self.author)) + \
		  "," + str(article_text) + "," + str(format_date(self.date_published)) + \
		  "," + str(db_escape(self.date_retrieved)) + ""
		return query

# WARNING:
# Trying to do anything useful with EVERY article is insane, there are
# going to be loads, so make sure an SQL condition is set
def db_get_all_articles(sql_conditions=None):
	# we need a DictCursor for this one
	db = connect_to_database()
	cur = db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
	query = "SELECT * FROM articles"

	if sql_conditions:
		# so basically sql_conditions needs to be in SQL format - none of that easy-to-use stuff
		# it just complicates things.
		query += " WHERE " + sql_conditions
	cur.execute(query)
	results = cur.fetchall()
	article_list = [Article(db_values = a) for a in results]
        cur.close()
	return article_list