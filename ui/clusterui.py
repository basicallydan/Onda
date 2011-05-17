'''
Created on 28 Jan 2010

@author: Daniel Hough
'''

from retrieval import article
from unigrammodel import clustermodel
from unigrammodel import clustering
from unigrammodel import articleunigram
import wx

ID_START_CLUSTERING = 101
ID_METHOD_SELECTED = 102
ID_TYPE_SELECTED = 103
ID_CLUSTER_SELECTED = 104
ID_ARTICLE_SELECTED = 105

class ClusterMonitor(wx.Frame):
    def __init__(self,parent,title,models,inv_index):
        # a -1 parameter instructs wxWidgets to use the default size
        wx.Frame.__init__(self,parent,wx.ID_ANY,title = title,size=(1280,768))
        panel = wx.Panel(self,-1)
        self.models = models
        self.inv_index = inv_index
        
        hs_main = wx.BoxSizer(wx.VERTICAL)
        
        self.hs_settings_sizer = self.create_settings_bar(panel)
        self.hs_info_sizer = self.create_cluster_info(panel)
        self.hs_monitor_sizer = self.create_monitor_grid(panel)
        
        hs_main.Add(self.hs_settings_sizer,0,wx.RIGHT | wx.LEFT | wx.TOP | wx.EXPAND,10)
        hs_main.Add(self.hs_info_sizer,0,wx.RIGHT | wx.LEFT | wx.BOTTOM | wx.TOP | wx.EXPAND,10)
        hs_main.Add(self.hs_monitor_sizer,1,wx.RIGHT | wx.LEFT | wx.BOTTOM | wx.TOP | wx.EXPAND,10)
        
        self.bind_selection_events()
        self.set_starting_values()
        
        panel.SetSizer(hs_main)
        
        self.statusbar = self.CreateStatusBar()
        self.bind_selection_events()
        self.Centre()
        self.Show()
    
    def set_starting_values(self):
        self.tc_num_models.SetValue(str(len(self.models)))
    
    def create_settings_bar(self,panel):
        lbl_cluster_methods = wx.StaticText(panel,-1,"Cluster Method")
        self.cb_cluster_methods = wx.ComboBox(panel, ID_METHOD_SELECTED, '', (-1,-1),(-1,-1), [str(clmethod) for clmethod in clustermodel.ClusterModel.cluster_methods.values()], wx.CB_READONLY)
        
        lbl_cluster_types = wx.StaticText(panel,-1,"Cluster Type")
        self.cb_cluster_types = wx.ComboBox(panel, ID_TYPE_SELECTED, '', (-1,-1),(-1,-1), [str(cltype) for cltype in clustering.ClusterMaker.cluster_types.values()], wx.CB_READONLY)
        
        lbl_threshold = wx.StaticText(panel,-1,"Similarity Threshold")
        self.tc_threshold = wx.TextCtrl(panel,-1,"0.22")
        
        self.bt_start = wx.Button(panel, ID_START_CLUSTERING, label="Begin!")
        
        hs_settings_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        hs_settings_sizer.Add(lbl_cluster_methods,0,wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT,5)
        hs_settings_sizer.Add(self.cb_cluster_methods,1,5)
        
        hs_settings_sizer.Add(lbl_cluster_types,0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT,5)
        hs_settings_sizer.Add(self.cb_cluster_types,1,5)
        
        hs_settings_sizer.Add(lbl_threshold,0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT,5)
        hs_settings_sizer.Add(self.tc_threshold,0,5)
        
        hs_settings_sizer.Add(self.bt_start,0,5)
        
        return hs_settings_sizer
    
    def create_cluster_info(self,panel):
        large_font = wx.Font(15, wx.SWISS, wx.NORMAL, wx.BOLD)
        
        lbl_num_clusters = wx.StaticText(panel,-1,"Number of Clusters:")
        self.tc_num_clusters = wx.TextCtrl(panel,-1,"0")
        lbl_num_clusters.SetFont(large_font)
        self.tc_num_clusters.SetFont(large_font)
        
        lbl_num_models = wx.StaticText(panel,-1,"Number of Models:")
        self.tc_num_models = wx.TextCtrl(panel,-1,"0")
        lbl_num_models.SetFont(large_font)
        self.tc_num_models.SetFont(large_font)
        
        hs_info_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        hs_info_sizer.Add(lbl_num_models, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT,5)
        hs_info_sizer.Add(self.tc_num_models, 1, wx.EXPAND)
        
        hs_info_sizer.Add(lbl_num_clusters, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT,5)
        hs_info_sizer.Add(self.tc_num_clusters, 1, wx.EXPAND)
        
        return hs_info_sizer
    
    def create_monitor_grid(self,panel):
        large_font = wx.Font(15, wx.SWISS, wx.NORMAL, wx.BOLD)
        
        lbl_unclustered = wx.StaticText(panel,-1,"Unclustered Models")
        lbl_unclustered.SetFont(large_font)
        self.lb_models = wx.ListBox(panel, ID_ARTICLE_SELECTED, (-1,-1),(-1,-1), [model.article.title for model in models.values()])
        
        lbl_clusters = wx.StaticText(panel,-1,"Clusters")
        lbl_clusters.SetFont(large_font)
        self.lb_clusters = wx.ListBox(panel, ID_CLUSTER_SELECTED, (-1,-1),(-1,-1))
        
        vs_models_clusters_sizer = wx.BoxSizer(wx.VERTICAL)
        vs_models_clusters_sizer.Add(lbl_unclustered, 0, wx.ALIGN_CENTER | wx.RIGHT | wx.LEFT,5)
        vs_models_clusters_sizer.Add(self.lb_models,1,wx.EXPAND)
        vs_models_clusters_sizer.Add(lbl_clusters, 0, wx.ALIGN_CENTER | wx.RIGHT | wx.LEFT,5)
        vs_models_clusters_sizer.Add(self.lb_clusters,1,wx.EXPAND)
        
        lbl_cluster_info = wx.StaticText(panel,-1,"Cluster Info")
        lbl_cluster_info.SetFont(large_font)
        
        fs_cluster_info = self.create_cluster_info_grid(panel)
        
        vs_cluster_info_sizer = wx.BoxSizer(wx.VERTICAL)
        vs_cluster_info_sizer.Add(lbl_cluster_info,0,wx.ALIGN_CENTER | wx.RIGHT | wx.LEFT,5)
        vs_cluster_info_sizer.Add(fs_cluster_info,1,wx.EXPAND)
        
        hs_monitor_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hs_monitor_sizer.Add(vs_models_clusters_sizer, 1, wx.EXPAND | wx.RIGHT,5)
        hs_monitor_sizer.Add(vs_cluster_info_sizer, 1, wx.EXPAND | wx.LEFT,5)
        
        return hs_monitor_sizer
    
    def create_cluster_info_grid(self,panel):
        lbl_num_models_in_cluster = wx.StaticText(panel,-1,"Number of Models:")
        self.tc_num_models_in_cluster = wx.TextCtrl(panel,-1,"0")
        
        lbl_models_in_cluster = wx.StaticText(panel,-1,"Models:")
        self.lb_models_in_cluster = wx.ListBox(panel)
        
        fs_cluster_info = wx.FlexGridSizer(cols=2,hgap=5,vgap=5)
        fs_cluster_info.AddGrowableCol(1)
        
        fs_cluster_info.Add(lbl_num_models_in_cluster, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fs_cluster_info.Add(self.tc_num_models_in_cluster, 0, wx.EXPAND)
        
        fs_cluster_info.Add(lbl_models_in_cluster, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fs_cluster_info.Add(self.lb_models_in_cluster, 0, wx.EXPAND)
        
        return fs_cluster_info
        
    def bind_selection_events(self):
        wx.EVT_COMBOBOX(self, ID_METHOD_SELECTED, self.select_cluster_method)
        wx.EVT_COMBOBOX(self, ID_TYPE_SELECTED, self.select_cluster_type)
        wx.EVT_BUTTON(self, ID_START_CLUSTERING, self.start_clustering)
        wx.EVT_LISTBOX(self, ID_CLUSTER_SELECTED, self.get_cluster_info)
    
    def select_cluster_method(self,e = None):
        if e:
            self.cluster_method = int(e.GetSelection())
            print "Setting cluster method to " + str(self.cluster_method)
    
    def select_cluster_type(self,e = None):
        if e:
            self.cluster_type = int(e.GetSelection())
            print "Setting cluster type to " + str(self.cluster_type)
    
    def get_cluster_info(self,e = None):
        if e:
            self.selected_cluster = int(self.lb_clusters.GetSelection(int(e.GetSelection())))
            print str(self.selected_cluster)
    
    def start_clustering(self,e = None):
        if e:
            clusterer = clustering.ClusterMaker(cluster_type = self.cluster_type)
            cluster_thread = clustering.ClustererThread(clusterer,self.models,self.inv_index,float(self.tc_threshold.GetValue()),self.cluster_method,on_change=self.update)
            cluster_thread.start()
            # clusterer.cluster_articles(self.models,self.inv_index,float(self.tc_threshold.GetValue()),self.cluster_method,on_change=self.update)
            # clusterer.run(self.models,self.inv_index,float(self.tc_threshold.GetValue()),self.cluster_method,on_change=self.update,name = "whatever")
            
    def update(self,clusters=None,new_cluster=None,remove_model=None):
        if clusters:
            self.tc_num_clusters.SetValue(str(len(clusters)))
            self.tc_num_clusters.Update()
            self.clusters = clusters
        if new_cluster:
            self.lb_clusters.AppendAndEnsureVisible(str(new_cluster))
            self.lb_clusters.Update()

theVar = 1

app = wx.App(False)
man_articles = article.db_get_all_articles("NOT trainingcluster = 0")
models,inv_index = articleunigram.db_load_models(man_articles)
frame = ClusterMonitor(None,'Article Browser',models,inv_index)
app.MainLoop()