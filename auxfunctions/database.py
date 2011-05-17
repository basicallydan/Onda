'''
Created on 20 Jan 2010

@author: Daniel Hough

Some helpful database functions
'''
import MySQLdb
import rfc822
import time

def db_escape(val):
    '''
    Escapes all the necessary characters, or if they arent found returns NULL
    '''
    val = str(val).strip()
    if val == None or val == "None": val = None
    if val:
        return MySQLdb.string_literal(val)
    else:
        return "NULL"

def get_first_column(results):
    return [val[0] for val in list(results)]

def format_date(date):
    '''
    Formats a date properly from an RFC822 format (used by RSS)
    Into the Python format, then into the MySQL format
    '''
    python_date = rfc822.parsedate(date)
    mysql_date = time.strftime("%Y-%m-%d %H:%M:%S", python_date)
    return "'" + mysql_date + "'"

def connect_to_database():
    return MySQLdb.connect(host="localhost", user="dan_dissertation",passwd="onda500",db="dissertation")