'''
Created on 28 Jan 2010

@author: Daniel Hough
'''

from retrieval import article
from retrieval import source
from clustering import cluster
import wx
import re

ID_CONNECT = 101
ID_SOURCE_SELECTED = 102
ID_ARTICLE_SELECTED = 103
ID_CLUSTER_SELECTED = 104
ID_ADD_CLUSTER = 105
ID_DEL_CLUSTER = 106
ID_EDIT_CLUSTER = 107
ID_SEARCH_ARTICLES = 108
ID_SEARCH_CLUSTERS = 109

class ArticleBrowser(wx.Frame):
    def __init__(self,parent,title,sources,clusters = None):
        # a -1 parameter instructs wxWidgets to use the default size
        wx.Frame.__init__(self,parent,wx.ID_ANY,title = title,size=(1280,768))
        self.create_menu()
        self.statusbar = self.CreateStatusBar()
        self.selected_source_index = 0
        self.previous_search_length = 0
        
        self.sources = sources
        self.clusters = clusters
        
        panel = wx.Panel(self,-1)
        
        hs_main = wx.BoxSizer(wx.HORIZONTAL)
        
        # create the left-hand vsizer, add bits to it
        self.vs_left_sizer = wx.BoxSizer(wx.VERTICAL)        
        vs_left_sizer = self.create_article_browser(panel)
        
        # put it on the main hs
        hs_main.Add(vs_left_sizer,1,wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 10)
        
        vs_article_info = wx.BoxSizer(wx.VERTICAL)
        hs_article_name = wx.BoxSizer(wx.HORIZONTAL)
        st_article = wx.StaticText(panel, -1, "Article Name")
        self.tc_article_title = wx.TextCtrl(panel, -1)
        hs_article_name.Add(st_article, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)
        hs_article_name.Add(self.tc_article_title,1)
        vs_article_info.Add(hs_article_name)
        
        self.tc_article_text = wx.TextCtrl(panel, -1, style=wx.TE_MULTILINE)
        vs_article_info.Add(self.tc_article_text,1,wx.EXPAND | wx.TOP, 10)
        hs_main.Add(vs_article_info,1,wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 10)
        # hs_main.Add(self.tc_article_text,1,wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        
        panel.SetSizer(hs_main)
        
        self.bind_selection_events()
        self.Centre()
        self.Show()
    
    def create_article_browser(self,panel):
        vs_left_sizer = wx.BoxSizer(wx.VERTICAL)
        self.tc_article_search = wx.TextCtrl(panel, ID_SEARCH_ARTICLES)
        vs_left_sizer.Add(self.tc_article_search, 0)
        self.cb_sources = wx.ComboBox(panel, ID_SOURCE_SELECTED, '', (-1,-1),(270,-1), [], wx.CB_READONLY)
        vs_left_sizer.Add(self.cb_sources, 0,wx.EXPAND | wx.TOP | wx. BOTTOM,5)
        self.lb_articles = wx.ListBox(panel, ID_ARTICLE_SELECTED, (-1,-1),(-1,-1), [], wx.LB_MULTIPLE)
        vs_left_sizer.Add(self.lb_articles, 1,wx.EXPAND | wx.TOP | wx. BOTTOM,5)
        
        vs_clusters = self.create_cluster_browser(panel)
        vs_left_sizer.Add(vs_clusters, 1, wx.EXPAND | wx.TOP | wx. BOTTOM,5)
        return vs_left_sizer
    
    def create_cluster_browser(self,panel):
        vs_clusters = wx.BoxSizer(wx.VERTICAL)
        self.tc_cluster_search = wx.TextCtrl(panel, ID_SEARCH_CLUSTERS)
        vs_clusters.Add(self.tc_cluster_search, 0)
        self.lb_clusters = wx.ListBox(panel, ID_CLUSTER_SELECTED, (-1,-1),(270,130), [], wx.LB_SINGLE)
        vs_clusters.Add(self.lb_clusters, 1, wx.EXPAND | wx.TOP | wx. BOTTOM,5)
        
        self.bt_del_cluster = wx.Button(panel, ID_DEL_CLUSTER, label="Delete")
        self.bt_add_cluster = wx.Button(panel, ID_ADD_CLUSTER, label="New")
        self.bt_edit_cluster = wx.Button(panel, ID_EDIT_CLUSTER, label="Edit")
        hs_cluster_buttons = wx.BoxSizer(wx.HORIZONTAL)
        hs_cluster_buttons.Add(self.bt_del_cluster,0,wx.ALIGN_LEFT)
        hs_cluster_buttons.Add(self.bt_edit_cluster,0)
        hs_cluster_buttons.Add(self.bt_add_cluster,0,wx.ALIGN_RIGHT)
        vs_clusters.Add(hs_cluster_buttons, 0, wx.EXPAND)
        
        return vs_clusters
        
    def create_menu(self):
        self.menu_bar = wx.MenuBar()
        self.db_menu = wx.Menu()
        self.db_connect = wx.MenuItem(self.db_menu, ID_CONNECT, '&Connect')
        self.db_menu.AppendItem(self.db_connect)
        self.menu_bar.Append(self.db_menu,"&Database")
        
        self.Bind(wx.EVT_MENU,self.connect_to_database,id=ID_CONNECT)
        
        self.SetMenuBar(self.menu_bar)
        
    def bind_selection_events(self):
        wx.EVT_COMBOBOX(self, ID_SOURCE_SELECTED, self.show_article_titles)
        wx.EVT_LISTBOX(self, ID_ARTICLE_SELECTED, self.show_article_content)
        wx.EVT_LISTBOX_DCLICK(self, ID_CLUSTER_SELECTED, self.add_to_cluster)
        
        wx.EVT_BUTTON(self, ID_ADD_CLUSTER, self.create_cluster)
        wx.EVT_BUTTON(self, ID_DEL_CLUSTER, self.delete_cluster)
        wx.EVT_BUTTON(self, ID_EDIT_CLUSTER, self.edit_cluster)
        
        wx.EVT_TEXT(self, ID_SEARCH_ARTICLES, self.search_for_article)
        wx.EVT_TEXT(self, ID_SEARCH_CLUSTERS, self.search_for_cluster)

    def connect_to_database(self,e = None):
        self.cb_sources.Clear()
        self.cb_sources.Append("All")
        self.cb_sources.Select(0)
        for news_source in self.sources:
            self.cb_sources.Append(news_source.website_name,news_source)
        for c in self.clusters:
            self.lb_clusters.Append(c.description,c.id)
    
    def show_article_titles(self,e=None):
        if e:
            self.selected_source_index = e.GetSelection()
        if self.selected_source_index == 0:
            articles = article.db_get_all_articles("`trainingcluster` = '0' AND NOT source = 'express'")
        else:
            selected_source = self.cb_sources.GetClientData(self.selected_source_index)
            articles = selected_source.db_load_articles(sql_conditions = "`trainingcluster` = '0'",force_query=True)
            self.cb_sources.SetString(self.selected_source_index,str(selected_source.website_name + " (" + str(len(articles)) + " unclustered articles)"))
        self.lb_articles.Clear()
        for news_article in articles:
            self.lb_articles.Append(news_article.title,news_article)
    
    def show_cluster_titles(self):
        self.lb_clusters.Clear()
        for c in self.clusters:
            self.lb_clusters.Append(c.description,c.id)
    
    def show_article_content(self,e):
        article_index = e.GetSelection()
        article_content = self.lb_articles.GetClientData(article_index).article_text
        article_title = self.lb_articles.GetClientData(article_index).title
        self.tc_article_text.SetValue(article_content)
        self.tc_article_title.SetValue(article_title)
    
    def create_cluster(self,e):
        dialog = wx.TextEntryDialog(self,"Name of Cluster", 'Enter cluster name')
        new_cluster_name = None
        if dialog.ShowModal() == wx.ID_OK:
            new_cluster_name = str(dialog.GetValue())
        new_cluster = cluster.TrainingCluster(description=new_cluster_name)
        clusters.append(new_cluster)
        self.lb_clusters.Append(new_cluster.description,new_cluster.id)
    
    def delete_cluster(self,e):
        pass
    
    def edit_cluster(self,e):
        pass
    
    def search_for_article(self,e):
        search_term = e.GetString()
        self.lb_articles.DeselectAll()
        if len(search_term) > 0:
            if len(search_term) <= self.previous_search_length:
                self.show_article_titles()
            self.previous_search_length = len(search_term)
            matches = 0
            for list_item in self.lb_articles.GetItems():
                term_list = search_term.split()
                re_search_pattern = "(" + str("+|".join(term_list)) + "+)"
                # if search_term.lower() not in list_item.lower():
                if not re.search(re_search_pattern,list_item,re.I):
                    item_index = self.lb_articles.FindString(list_item)
                    self.lb_articles.Delete(item_index)
                else:
                    matches += 1
                    item_index = self.lb_articles.FindString(list_item)
                    # self.lb_articles.Select(item_index)
                    self.statusbar.SetStatusText("Searching for " + search_term + ": " + str(matches) + " matches found")
            if matches == 0:
                self.statusbar.SetStatusText("No matches for " + search_term + " found")
        else:
            self.show_article_titles()
    
    def search_for_cluster(self,e):
        search_term = e.GetString()
        self.lb_clusters.DeselectAll()
        if len(search_term) > 0:
            if len(search_term) <= self.previous_search_length:
                self.show_cluster_titles()
            self.previous_search_length = len(search_term)
            matches = 0
            for list_item in self.lb_clusters.GetItems():
                term_list = search_term.split()
                re_search_pattern = "(" + str("+|".join(term_list)) + "+)"
                # if search_term.lower() not in list_item.lower():
                if not re.search(re_search_pattern,list_item,re.I):
                    item_index = self.lb_clusters.FindString(list_item)
                    self.lb_clusters.Delete(item_index)
                else:
                    matches += 1
                    item_index = self.lb_clusters.FindString(list_item)
                    # self.lb_clusters.Select(item_index)
                    self.statusbar.SetStatusText("Searching for cluster " + search_term + ": " + str(matches) + " matches found")
            if matches == 0:
                self.statusbar.SetStatusText("No matches for " + search_term + " found")
        else:
            self.show_cluster_titles()
    
    def add_to_cluster(self,e):
        selected_article_items = self.lb_articles.GetSelections()
        selected_articles = [self.lb_articles.GetClientData(id) for id in selected_article_items]
        cluster_index = e.GetSelection()
        cluster_id = self.lb_clusters.GetClientData(cluster_index)
        success = True
        for selected_article in selected_articles:
            if not selected_article.db_set_classification(cluster_id):
                success = False
        if success:
            # make sure the list is ordered from highest to lowest or the indices
            # will be changed each time
            selected_item_list = list(selected_article_items)
            selected_item_list.sort()
            selected_item_list.reverse()
            numitems = len(selected_item_list)
            if numitems == 1:
                self.lb_articles.Delete(selected_item_list[0])
            else:
                for index in selected_item_list:
                    self.lb_articles.Delete(index)
            self.statusbar.SetStatusText("Correctly added " + str(len(selected_item_list)) + " article" + ("s " if numitems > 1 else " ") + \
                                         "to the cluster " + str(self.lb_clusters.GetString(cluster_index)))
        else:
            wx.MessageBox("Error!", 'Error')

sources = source.get_all_sources()
clusters = cluster.get_all_training_clusters()
app = wx.App(False)
frame = ArticleBrowser(None,'Article Browser',sources,clusters)
app.MainLoop()