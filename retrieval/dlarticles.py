'''
Created on 12 Feb 2010

@author: Daniel Hough
'''
import datetime
import sys
import os
import MySQLdb
import logging
from source import NewsSource

def run_all_sources():
    now = datetime.datetime.now()
    folder = str(now.year) + "-" + str(now.month)
    folder = str(sys.path[0]) + folder
    if not os.path.exists(folder):
        os.makedirs(folder)
    file = str(now.day) + "_" + str(now.hour) + "-" + str(now.minute) + ".txt"
    path = folder + "/" + file
    report_file = open(path,"w")
    
    log_filename = folder + "/articledownloads.log"
    logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%H:%M',
                        filename=log_filename,
                        filemode='w')
    
    db = MySQLdb.connect(host="localhost", user="dan_dissertation",passwd="onda500",db="dissertation")
    
    guardian = NewsSource("theguardian",db,now)
    report_file.write("Finding " + str(guardian.website_name) + "articles...\n")
    guardian.print_info()
    for article_ret in guardian.web_download_articles():
        report_file.write(str(article_ret) + "\n")
    report_file.write("Articles affected: " + str(guardian.rows_affected) + "\n")
    report_file.write("Duplicates found: " + str(guardian.duplicates_found) + "\n")

    dailymail = NewsSource("dailymail",db,now)
    report_file.write("Finding " + str(dailymail.website_name) + "articles...\n")
    dailymail.print_info()
    for article_ret in dailymail.web_download_articles():
        report_file.write(str(article_ret) + "\n")
    report_file.write("Articles affected: " + str(dailymail.rows_affected) + "\n")
    report_file.write("Duplicates found: " + str(dailymail.duplicates_found) + "\n")
    
    express = NewsSource("express",db,now)
    report_file.write("Finding " + str(express.website_name) + "articles...\n")
    express.print_info()
    for article_ret in express.web_download_articles():
        report_file.write(str(article_ret) + "\n")
    report_file.write("Articles affected: " + str(express.rows_affected) + "\n")
    report_file.write("Duplicates found: " + str(express.duplicates_found) + "\n")
    
    telegraph = NewsSource("thedailytelegraph",db,now)
    report_file.write("Finding " + str(telegraph.website_name) + " articles...\n")
    telegraph.print_info()
    for article_ret in telegraph.web_download_articles():
        report_file.write(str(article_ret) + "\n")
    report_file.write("Articles affected: " + str(telegraph.rows_affected) + "\n")
    report_file.write("Duplicates found: " + str(telegraph.duplicates_found) + "\n")
    
    report_file.close()
    
run_all_sources()