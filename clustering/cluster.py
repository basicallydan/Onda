'''
Created on 28 Jan 2010

@author: Dan
'''

from auxfunctions.database import connect_to_database
import MySQLdb

class ArticleCluster(object):
    '''
    This has yet to be made
    '''


    def __init__(self,params):
        '''
        Constructor
        '''

class TrainingCluster(object):
    '''
    This is for training the system, you can give an article
    a training cluster dontchaknow.
    '''
    def __init__(self,id=None,description=None):
        if id:
            if description:
                self.id = id
                self.description = description
            else:
                self.db = connect_to_database()
                # must be a cluster already on the database
                c = self.db.cursor()
                query = "SELECT * FROM training_clusters WHERE `id` = '" + str(id) + "'"
                c.execute(query)
                result = c.fetchone()
                if result:
                    self.id = id
                    self.description = result[1]
        elif description:
            self.db = connect_to_database()
            # obviously doesn't exist yet, let's make it
            self.description = description
            c = self.db.cursor()
            query = "INSERT INTO training_clusters(`description`) VALUES ('" + str(description) + "')"
            c.execute(query)
            self.id = c.lastrowid

def get_all_training_clusters():
    db = connect_to_database()
    c = db.cursor()
    query = "SELECT * FROM training_clusters"
    c.execute(query)
    result = c.fetchall()
    return [TrainingCluster(tc[0],tc[1]) for tc in result]