import time
from pypetree.ui.wizards.wizard import *
from pypetree.model.point_cloud import *
from pypetree.model.reconstruction.modified_vl_reconstruction import *


class MVLWizard(Wizard):

    def run(self):
        if self.parent.scene.get_active_point_cloud():
            self.model = ModifiedVerroustLazarusReconstruction(
                             P=self.parent.scene.get_active_point_cloud().P)
            if self.parent.scene.get_active_point_cloud().up is not None:
                self.pages[1].ydim_tf.SetValue(
                              str(self.parent.scene.get_active_point_cloud().up))
            else:
                self.pages[1].ydim_tf.SetValue(
                              str(guess_point_cloud_height_dimension(self.model.P)))
        else:
            self.parent.status_bar.SetStatusText(
                                   'A point cloud is required for this!')
            return False
        Wizard.run(self)

    def on_finish(self, e):
        new_model_name = '%s_k=%s_r=%s_d=%s_mccs=%s_w=%s' % \
            (self.parent.scene.get_active_point_cloud().name,
             self.pages[0].k_tf.GetValue(), self.pages[0].r_tf.GetValue(),
             self.pages[1].d_tf.GetValue(), self.pages[1].mccs_tf.GetValue(),
             self.pages[3].w_tf.GetValue())
        self.parent.scene.update_polytube_model_name('L', new_model_name)
        self.curr_page.Hide()
        self.Hide()

def set_nn_connected_components_color_scheme(self, graph_list):
    colors = ['red', 'orange', 'green', 'cyan', 'blue',
              'brown', 'orangered', 'purple']
    color_scheme = []
    color_idx = 0
    for g in graph_list:
        color_scheme.append((colors[color_idx], g.nodes()))
        color_idx += 1
        color_idx %= len(colors)
    self.scene.set_point_cloud_color_scheme(color_scheme)

    
WizardPage.set_nn_connected_components_color_scheme = \
  set_nn_connected_components_color_scheme

  
class MVLGeodesicConnectivityWizardPage(WizardPage):

    def __init__(self, wiz):
        WizardPage.__init__(self, wiz, 'Connectivity (Step %d/%d)' %
                                           (len(wiz.pages)+1, wiz.n_steps))
        k_lbl = wx.StaticText(self, wx.ID_ANY,
                              'Number of nearest neighbors (k):', size=(250,-1))
        self.k_tf = wx.TextCtrl(self, wx.ID_ANY, '10')
        k_sizer = wx.BoxSizer(wx.HORIZONTAL)
        k_sizer.Add(k_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        k_sizer.Add(self.k_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        r_lbl = wx.StaticText(self, wx.ID_ANY,
                              'Max nearest neighbors dist (r):', size=(250,-1))
        self.r_tf = wx.TextCtrl(self, wx.ID_ANY, 'inf')
        r_sizer = wx.BoxSizer(wx.HORIZONTAL)
        r_sizer.Add(r_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        r_sizer.Add(self.r_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        # this is stupid!
        hspace_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hspace_sizer.Add(wx.StaticText(self, wx.ID_ANY, '', size=(250,75)),
                         0, wx.ALIGN_CENTER_VERTICAL, 10)
        self.sizer.Add(k_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(r_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(hspace_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.SetSizerAndFit(self.sizer)

    def on_run(self, e):
        if sys.platform == 'win32':
            self.wiz.nav_pnl.SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
        else:
            wx.BeginBusyCursor()
        wx.Yield()
        self.status_bar.SetStatusText('Computing nearest neighbors..')
        self.wiz.model.compute_nearest_neighbors(k=int(self.k_tf.GetValue()),
                                                 r=float(self.r_tf.GetValue()))
        n_comps, n_nodes_biggest, density = \
                                       self.wiz.model.get_connectivity_infos()
        self.scene.set_point_cloud_graph(self.wiz.model.N_full)
        self.set_nn_connected_components_color_scheme(
                                                   self.wiz.model.N_components)
        if sys.platform == 'win32':
            self.wiz.nav_pnl.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        else:
            wx.EndBusyCursor()
        st = 'Found %s connected component%s (biggest has %s nodes; ' \
             'overall density: %f)' % \
                (n_comps, 's' if n_comps > 1 else '', n_nodes_biggest, density)
        self.status_bar.SetStatusText(st)
        self.wiz.nav_pnl.next_btn.Enable(True)
        self.is_dirty = False
        self.next.is_dirty = True

    def on_enter(self, e):
        self.update_nav_buttons_and_show()
        if not self.is_dirty:
            self.scene.set_point_cloud_graph(self.wiz.model.N_full)
            self.set_nn_connected_components_color_scheme(self.wiz.model.N_components)

    def on_leave(self, e):
         self.scene.unset_point_cloud_graph()
         self.scene.get_active_point_cloud().reset_colors()
         self.Hide()

         
class MVLLevelSetWizardPage(WizardPage):

    def __init__(self, wiz):
        WizardPage.__init__(self, wiz,
                            'Level Sets (Step %d/%d)' % (len(wiz.pages)+1,
                                                         wiz.n_steps))
        ydim_lbl = wx.StaticText(self, wx.ID_ANY, 'Upward dimension [0,1,2]:',
                                 size=(250,-1))
        self.ydim_tf = wx.TextCtrl(self, wx.ID_ANY, '')
        ydim_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ydim_sizer.Add(ydim_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        ydim_sizer.Add(self.ydim_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        d_lbl = wx.StaticText(self, wx.ID_ANY, 'Level size:', size=(250,-1))
        self.d_tf = wx.TextCtrl(self, wx.ID_ANY, '0.5')
        d_sizer = wx.BoxSizer(wx.HORIZONTAL)
        d_sizer.Add(d_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        d_sizer.Add(self.d_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        mccs_lbl = wx.StaticText(self, wx.ID_ANY,
                                 'Min N-connected component size:',
                                 size=(250,-1))
        self.mccs_tf = wx.TextCtrl(self, wx.ID_ANY, '0')
        mccs_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mccs_sizer.Add(mccs_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        mccs_sizer.Add(self.mccs_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        self.bicol_cb = wx.CheckBox(self, wx.ID_ANY, 'Use only two colors')
        self.bicol_cb.SetValue(True)
        bicol_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bicol_sizer.Add(self.bicol_cb, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        #dc_lbl = wx.StaticText(self, wx.ID_ANY, 'Geodesic distance cap:',
        #                       size=(250,-1))
        #self.dc_tf = wx.TextCtrl(self, wx.ID_ANY, 'inf')
        #dc_sizer = wx.BoxSizer(wx.HORIZONTAL)
        #dc_sizer.Add(dc_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        #dc_sizer.Add(self.dc_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        self.sizer.Add(ydim_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(d_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(mccs_sizer, 0, wx.ALL|wx.EXPAND, 10)
        #self.sizer.Add(dc_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(bicol_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.SetSizerAndFit(self.sizer)

    def set_level_set_color_scheme(self):
        if self.bicol_cb.GetValue():
            ls_colors = ['red', 'limegreen']
        else:
            ls_colors = ['red', 'blue', 'orange', 'green', 'yellow',
                         'cyan', 'pink', 'orangered', 'purple']
        color_idx = 0
        ls_color_scheme = []
        for level, pts in self.wiz.model.level_sets.items():
            ls_color_scheme.append((ls_colors[color_idx], pts))
            color_idx += 1
            color_idx %= len(ls_colors)
        self.scene.set_point_cloud_color_scheme(ls_color_scheme)

    def on_run(self, e):
        if sys.platform == 'win32':
            self.wiz.nav_pnl.SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
        else:
            wx.BeginBusyCursor()
        wx.Yield()
        start = time.time()
        self.status_bar.SetStatusText('Computing shortest paths..')
        self.wiz.model.compute_shortest_paths(ydim=int(self.ydim_tf.GetValue()))
        self.status_bar.SetStatusText('Computing level sets..')
        n_ls = self.wiz.model.compute_level_sets(level_size=float(
            self.d_tf.GetValue()),
            min_connected_component_size=int(self.mccs_tf.GetValue()))
        self.set_level_set_color_scheme()
        #self.scene.setPointCloudColorScheme([('yellow', self.wiz.model.lsp)])
        if sys.platform == 'win32':
            self.wiz.nav_pnl.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        else:
            wx.EndBusyCursor()
        st = 'Found %d level sets (in %d seconds)' % \
                (n_ls, time.time() - start)
        self.status_bar.SetStatusText(st)
        self.wiz.nav_pnl.next_btn.Enable(True)
        self.is_dirty = False
        self.next.is_dirty = True

    def on_enter(self, e):
        self.update_nav_buttons_and_show()
        if not self.is_dirty:
            self.set_level_set_color_scheme()

    def on_leave(self, e):
        self.scene.unset_point_cloud_color_scheme()
        self.Hide()

        
class MVLReconstructionWizardPage(WizardPage):

    def __init__(self, wiz):

        WizardPage.__init__(self, wiz,
                            'Reconstruction (Step %s/%s)' %
                            (len(wiz.pages)+1, wiz.n_steps))
        # self.greedy_cb = wx.CheckBox(self, wx.ID_ANY,
        #                   'Use greedy search (quicker)')
        # self.greedy_cb.SetValue(True)
        # greedy_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # greedy_sizer.Add(self.greedy_cb, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        # self.extend_cb = wx.CheckBox(self, wx.ID_ANY,
        #                              'Extend terminal segments')
        # self.extend_cb.SetValue(True)
        # extend_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # extend_sizer.Add(self.extend_cb, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        self.vol_cb = wx.CheckBox(self, wx.ID_ANY,
                                  'Use volume reconstruction/smoothing')
        self.vol_cb.SetValue(True)
        vol_sizer = wx.BoxSizer(wx.HORIZONTAL)
        vol_sizer.Add(self.vol_cb, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        self.show_vol_cb = wx.CheckBox(self, wx.ID_ANY, 'Show volume')
        self.show_vol_cb.SetValue(True)
        show_vol_sizer = wx.BoxSizer(wx.HORIZONTAL)
        show_vol_sizer.Add(self.show_vol_cb, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        self.show_tips_cb = wx.CheckBox(self, wx.ID_ANY, 'Highlight tips')
        self.show_tips_cb.SetValue(True)
        show_tips_sizer = wx.BoxSizer(wx.HORIZONTAL)
        show_tips_sizer.Add(self.show_tips_cb, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        # self.sizer.Add(greedy_sizer, 0, wx.ALL|wx.EXPAND, 10)
        # self.sizer.Add(extend_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(vol_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(show_vol_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(show_tips_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.SetSizerAndFit(self.sizer)

    def on_run(self, e):
        if sys.platform == 'win32':
            self.wiz.nav_pnl.SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
        else:
            wx.BeginBusyCursor()
        wx.Yield()
        self.status_bar.SetStatusText('Segmenting level sets..')
        self.wiz.model.segmentation()

        ##########################################################
        # self.scene.setPointCloudGraph(self.wiz.model.level_to_graph[-1])
        # self.set_nn_connected_components_color_scheme(
        #                            self.wiz.model.level_to_segment_graphs[-1])

        # wx.EndBusyCursor()
        # return
        ##########################################################

        self.status_bar.SetStatusText('Skeleton reconstruction..')
        #self.wiz.model.skeleton_reconstruction(use_greedy_search=
        #        self.greedy_cb.GetValue(),
        #        extend_terminal_segments=self.extend_cb.GetValue())
        self.wiz.model.skeleton_reconstruction()

        if self.show_tips_cb.GetValue():
            self.wiz.model.prune_skeleton()

        if self.vol_cb.GetValue():
            self.status_bar.SetStatusText('Volume reconstruction..')
            self.wiz.model.volume_reconstruction()

        def set_next_dirty(sphere):
            self.next.is_dirty = True

        # note that a callback on 'delete' is not necessary
        self.scene.add_polytube_model(self.wiz.model.K, 'K',
            color_tips_in_yellow=False, #self.show_tips_cb.GetValue(),
            show_volume=self.show_vol_cb.GetValue(),
            additional_sphere_callbacks=[('moved', set_next_dirty),
                                         ('cutAtAttachedNode', set_next_dirty),
                                         ('cut_aboveAttachedNode', set_next_dirty)])
        if sys.platform == 'win32':
            self.wiz.nav_pnl.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        else:
            wx.EndBusyCursor()
        dims = self.wiz.model.K.get_dimensions()
        st = 'Found %s tips (dims: %0.2f x %0.2f x %0.2f, surf: %0.2f)' % \
             (self.wiz.model.K.get_number_of_tips(), dims[0], dims[1], dims[2],
              self.wiz.model.K.get_surface())
        self.status_bar.SetStatusText(st)
        self.wiz.nav_pnl.next_btn.Enable(True)
        self.is_dirty = False
        self.next.is_dirty = True

    def on_enter(self, e):
        self.update_nav_buttons_and_show()
        if not self.is_dirty:
            self.scene.set_active_polytube_model('K')

    def on_leave(self, e):
        self.scene.unset_point_cloud_graph()
        self.scene.set_polytube_model_visibility('K', False)
        self.Hide()

        
class MVLSmoothingWizardPage(WizardPage):

    def __init__(self, wiz):

        WizardPage.__init__(self, wiz, 'Smoothing (Step %d/%d)' %
                            (len(wiz.pages)+1, wiz.n_steps))
        w_lbl = wx.StaticText(self, wx.ID_ANY,
                              'Size of smoothing window (w):', size=(250,-1))
        self.w_tf = wx.TextCtrl(self, wx.ID_ANY, '5')
        w_sizer = wx.BoxSizer(wx.HORIZONTAL)
        w_sizer.Add(w_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        w_sizer.Add(self.w_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        self.show_vol_cb = wx.CheckBox(self, wx.ID_ANY, 'Show volume')
        self.show_vol_cb.SetValue(True)
        show_vol_sizer = wx.BoxSizer(wx.HORIZONTAL)
        show_vol_sizer.Add(self.show_vol_cb, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        self.show_tips_cb = wx.CheckBox(self, wx.ID_ANY, 'Highlight tips')
        self.show_tips_cb.SetValue(True)
        show_tips_sizer = wx.BoxSizer(wx.HORIZONTAL)
        show_tips_sizer.Add(self.show_tips_cb, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        self.sizer.Add(w_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(show_vol_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(show_tips_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.SetSizerAndFit(self.sizer)

    def on_run(self, e):
        if sys.platform == 'win32':
            self.wiz.nav_pnl.SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
        else:
            wx.BeginBusyCursor()
        wx.Yield()
        self.status_bar.SetStatusText('Smoothing..')
        L = self.wiz.model.K.smooth(w=int(self.w_tf.GetValue()))
        self.scene.add_polytube_model(L, 'L',
                            color_tips_in_yellow=self.show_tips_cb.GetValue(),
                            show_volume=self.show_vol_cb.GetValue())
        if sys.platform == 'win32':
            self.wiz.nav_pnl.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        else:
            wx.EndBusyCursor()
        self.status_bar.SetStatusText('Found %d tips' % L.get_number_of_tips())
        self.wiz.nav_pnl.next_btn.Enable(True)
        self.is_dirty = False

    def on_enter(self, e):
        self.update_nav_buttons_and_show()
        if not self.is_dirty:
            self.scene.set_active_polytube_model('L')

    def on_leave(self, e):
        self.scene.set_polytube_model_visibility('L', False)
        self.Hide()
