import wx
from pypetree.model.point_cloud import *


class PointCloudOpacityDialog(wx.Dialog):

    def __init__(self, parent):

        def set_opacity(e):
            if self.scene.get_active_point_cloud():
                self.scene.get_active_point_cloud().actor.GetProperty().\
                  SetOpacity(self.slider.GetValue() /100.0)
                self.scene.frame.ren_win.Render()

        self.parent = parent
        wx.Dialog.__init__(self, self.parent, wx.ID_ANY, 'Point Cloud Opacity')
        self.scene = self.parent.scene
        self.slider = wx.Slider(self, wx.ID_ANY, 100, 0, 100,
                            wx.DefaultPosition, (250, -1),
                            wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.Bind(wx.EVT_SLIDER, set_opacity)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.slider, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        self.SetSizerAndFit(sizer)


class PointCloudDownsamplingDialog(wx.Dialog):

    def __init__(self, parent):

        wx.Dialog.__init__(self, parent, wx.ID_ANY, 'Point Cloud Downsampling')

        self.parent = parent
        self.scene = self.parent.scene
        self.status_bar = self.parent.status_bar

        q_lbl = wx.StaticText(self, wx.ID_ANY, 'Bin size:', size=(250,-1))
        self.q_tf = wx.TextCtrl(self, wx.ID_ANY, '0.01')
        q_sizer = wx.BoxSizer(wx.HORIZONTAL)
        q_sizer.Add(q_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        q_sizer.Add(self.q_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)

        self.centroid_rb = wx.RadioButton(self, wx.ID_ANY,
                                          'Bin Centroids', style=wx.RB_GROUP)
        self.grid_rb = wx.RadioButton(self, wx.ID_ANY, 'Grid')
        rbg_sizer = wx.BoxSizer(wx.HORIZONTAL)
        rbg_sizer.Add(self.centroid_rb, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        rbg_sizer.Add(self.grid_rb, 0, wx.ALIGN_CENTER_VERTICAL, 10)

        self.diff_cb = wx.CheckBox(self, wx.ID_ANY, 'Show diff')
        self.diff_cb.SetValue(True)
        diff_sizer = wx.BoxSizer(wx.HORIZONTAL)
        diff_sizer.Add(self.diff_cb, 0, wx.ALIGN_CENTER_VERTICAL, 10)

        run_btn = wx.Button(self, wx.ID_ANY, 'Run')
        cancel_btn = wx.Button(self, wx.ID_ANY, 'Cancel')
        self.done_btn = wx.Button(self, wx.ID_ANY, 'Done')
        self.done_btn.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.on_run, run_btn)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, cancel_btn)
        self.Bind(wx.EVT_BUTTON, self.on_done, self.done_btn)
        self.Bind(wx.EVT_CLOSE, lambda e: self.on_cancel(e))
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(run_btn, 0, wx.ALL|wx.EXPAND, 10)
        btn_sizer.Add(cancel_btn, 0, wx.ALL|wx.EXPAND, 10)
        btn_sizer.Add(self.done_btn, 0, wx.ALL|wx.EXPAND, 10)

        top_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer.Add(q_sizer, 0, wx.ALL|wx.EXPAND, 10)
        top_sizer.Add(rbg_sizer, 0, wx.ALL|wx.EXPAND, 10)
        top_sizer.Add(diff_sizer, 0, wx.ALL|wx.EXPAND, 10)
        top_sizer.Add(btn_sizer, 0, wx.ALL|wx.ALIGN_RIGHT, 10)

        self.SetSizerAndFit(top_sizer)

    def on_run(self, e):
        if not self.scene.get_active_point_cloud():
            self.status_bar.SetStatusText('A point cloud is required for this!')
            return
        if sys.platform == 'win32':
            self.SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
        else:
            wx.BeginBusyCursor()
        wx.Yield()
        self.parent.gauge_popup.Show()
        qpc = QuantizedPointCloud(self.scene.get_active_point_cloud().P)
        self.status_bar.SetStatusText('Downsampling point cloud..')
        mode = 'bin_centroids' if self.centroid_rb.GetValue() else 'grid'
        Q = qpc.downsample(float(self.q_tf.GetValue()), mode,
                           self.parent.gauge_popup,
                           ['Quantizing.. (1/2)', 'Downsampling.. (2/2)'])
        self.status_bar.SetStatusText('Downsampling: %d -> %d points' %
                            (len(self.scene.get_active_point_cloud().P), len(Q)))
        self.scene.get_active_point_cloud().set_visible(self.diff_cb.GetValue())
        # aggreg is a temp name
        self.scene.add_point_cloud(Q, 'aggreg', 'limegreen', set_active=False)
        self.parent.gauge_popup.Hide()
        if sys.platform == 'win32':
            self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        else:
            wx.EndBusyCursor()
        self.done_btn.Enable()

    def on_cancel(self, e):
        self.scene.delete_point_cloud('aggreg')
        self.scene.get_active_point_cloud().set_visible(True)
        self.status_bar.SetStatusText('')
        self.Hide()

    def on_done(self, e):
        source_pc_name = self.scene.get_active_point_cloud().name
        self.scene.delete_point_cloud(source_pc_name)
        pc = self.scene.get_point_cloud('aggreg')
        pc.base_color = 'red'
        mode = 'bin_centroids' if self.centroid_rb.GetValue() else 'grid'
        new_pc_name = '%s_%s_q=%s' % (source_pc_name, mode, self.q_tf.GetValue())
        self.scene.update_point_cloud_name(pc.name, new_pc_name)
        pc.reset_colors()
        self.scene.set_active_point_cloud(new_pc_name)
        self.Hide()


class PointCloudVoxelizationDialog(wx.Dialog):

    def __init__(self, parent):

        wx.Dialog.__init__(self, parent, wx.ID_ANY, 'Point Cloud Voxelization')

        self.parent = parent
        self.scene = self.parent.scene
        self.status_bar = self.parent.status_bar

        q_lbl = wx.StaticText(self, wx.ID_ANY, 'Bin size:', size=(250,-1))
        self.q_tf = wx.TextCtrl(self, wx.ID_ANY, '0.025')
        q_sizer = wx.BoxSizer(wx.HORIZONTAL)
        q_sizer.Add(q_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        q_sizer.Add(self.q_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)

        self.diff_cb = wx.CheckBox(self, wx.ID_ANY, 'Show Point Cloud')
        self.diff_cb.SetValue(True)
        diff_sizer = wx.BoxSizer(wx.HORIZONTAL)
        diff_sizer.Add(self.diff_cb, 0, wx.ALIGN_CENTER_VERTICAL, 10)

        run_btn = wx.Button(self, wx.ID_ANY, 'Run')
        cancel_btn = wx.Button(self, wx.ID_ANY, 'Cancel')
        self.done_btn = wx.Button(self, wx.ID_ANY, 'Done')
        self.done_btn.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.on_run, run_btn)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, cancel_btn)
        self.Bind(wx.EVT_BUTTON, self.on_done, self.done_btn)
        self.Bind(wx.EVT_CLOSE, lambda e: self.on_cancel(e))
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(run_btn, 0, wx.ALL|wx.EXPAND, 10)
        btn_sizer.Add(cancel_btn, 0, wx.ALL|wx.EXPAND, 10)
        btn_sizer.Add(self.done_btn, 0, wx.ALL|wx.EXPAND, 10)

        top_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer.Add(q_sizer, 0, wx.ALL|wx.EXPAND, 10)
        top_sizer.Add(diff_sizer, 0, wx.ALL|wx.EXPAND, 10)
        top_sizer.Add(btn_sizer, 0, wx.ALL|wx.ALIGN_RIGHT, 10)

        self.SetSizerAndFit(top_sizer)

    def on_run(self, e):
        if not self.scene.get_active_point_cloud():
            self.status_bar.SetStatusText('A point cloud is required for this!')
            return
        if sys.platform == 'win32':
            self.SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
        else:
            wx.BeginBusyCursor()
        wx.Yield()
        V = QuantizedPointCloud(self.scene.get_active_point_cloud().P)
        self.status_bar.SetStatusText('Voxelizing point cloud..')
        V.quantize(float(self.q_tf.GetValue()))
        dims = V.get_bin_dims()
        self.status_bar.SetStatusText('Voxelization: %d points -> %d voxels,' \
                                      ' grid: %d x %d x %d' %
                                       (len(self.scene.get_active_point_cloud().P),
                                        len(V), dims[0], dims[1], dims[2]))
        show_pc = self.diff_cb.GetValue()
        self.scene.add_voxel_model(V, 'default',
                                 0.5 if show_pc else 1, 'limegreen')
        self.scene.set_point_cloud_visibility('default', show_pc)
        if sys.platform == 'win32':
            self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        else:
            wx.EndBusyCursor()
        self.done_btn.Enable()

    def on_cancel(self, e):
        self.scene.get_active_voxel_model().delete()
        self.scene.set_point_cloud_visibility('default', True)
        self.status_bar.SetStatusText('')
        self.Hide()

    def on_done(self, e):
        self.scene.set_point_cloud_visibility('default', False)
        self.scene.get_active_voxel_model().actor.GetProperty().SetOpacity(1)
        self.scene.get_active_voxel_model().actor.GetProperty().\
          SetColor(*name_to_rgb_float('gray'))
        self.scene.frame.ren_win.Render()
        self.Hide()


class PointCloudGeoClippingDialog(wx.Dialog):

    def __init__(self, parent):

        wx.Dialog.__init__(self, parent, wx.ID_ANY, 'Geodesic Clipping')

        self.parent = parent
        self.scene = self.parent.scene
        self.status_bar = self.parent.status_bar

        ydim_lbl = wx.StaticText(self, wx.ID_ANY, 'Upward dimension [0,1,2]:',
                                 size=(250,-1))
        self.ydim_tf = wx.TextCtrl(self, wx.ID_ANY, '2')
        ydim_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ydim_sizer.Add(ydim_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        ydim_sizer.Add(self.ydim_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)

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

        d_lbl = wx.StaticText(self, wx.ID_ANY,
                              'Clipping distance (d):', size=(250,-1))
        self.d_tf = wx.TextCtrl(self, wx.ID_ANY, '1')
        d_sizer = wx.BoxSizer(wx.HORIZONTAL)
        d_sizer.Add(d_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        d_sizer.Add(self.d_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)

        self.diff_cb = wx.CheckBox(self, wx.ID_ANY, 'Show diff')
        self.diff_cb.SetValue(True)
        diff_sizer = wx.BoxSizer(wx.HORIZONTAL)
        diff_sizer.Add(self.diff_cb, 0, wx.ALIGN_CENTER_VERTICAL, 10)

        run_btn = wx.Button(self, wx.ID_ANY, 'Run')
        cancel_btn = wx.Button(self, wx.ID_ANY, 'Cancel')
        self.done_btn = wx.Button(self, wx.ID_ANY, 'Done')
        self.done_btn.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.on_run, run_btn)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, cancel_btn)
        self.Bind(wx.EVT_BUTTON, self.on_done, self.done_btn)
        self.Bind(wx.EVT_CLOSE, lambda e: self.on_cancel(e))
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(run_btn, 0, wx.ALL|wx.EXPAND, 10)
        btn_sizer.Add(cancel_btn, 0, wx.ALL|wx.EXPAND, 10)
        btn_sizer.Add(self.done_btn, 0, wx.ALL|wx.EXPAND, 10)

        top_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer.Add(ydim_sizer, 0, wx.ALL|wx.EXPAND, 10)
        top_sizer.Add(k_sizer, 0, wx.ALL|wx.EXPAND, 10)
        top_sizer.Add(r_sizer, 0, wx.ALL|wx.EXPAND, 10)
        top_sizer.Add(d_sizer, 0, wx.ALL|wx.EXPAND, 10)
        top_sizer.Add(diff_sizer, 0, wx.ALL|wx.EXPAND, 10)
        top_sizer.Add(btn_sizer, 0, wx.ALL|wx.ALIGN_RIGHT, 10)

        self.SetSizerAndFit(top_sizer)

        self.last_gcN_params = (None, None, None) # k, r, ydim

    def on_run(self, e):
        if not self.scene.get_active_point_cloud():
            self.status_bar.SetStatusText('A point cloud is required for this!')
            return
        if sys.platform == 'win32':
            self.SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
        else:
            wx.BeginBusyCursor()
        wx.Yield()
        k = int(self.k_tf.GetValue())
        r = float(self.r_tf.GetValue())
        d = float(self.d_tf.GetValue())
        ydim = int(self.ydim_tf.GetValue())
        if self.last_gcN_params != (k, r, ydim):
            self.status_bar.SetStatusText('Computing nearest neighbors..')
            self.gc = GeodesicClipping(self.scene.get_active_point_cloud().P)
            self.gc.nearest_neighbors(k, r, ydim)
            self.last_gcN_params = (k, r, ydim)
        self.status_bar.SetStatusText('Geodesic clipping..')
        P = self.gc.clip(d)
        self.scene.add_point_cloud(P, 'geo_clipping', 'green', False)
        self.scene.get_active_point_cloud().set_visible(self.diff_cb.GetValue())
        self.status_bar.SetStatusText('Geodesic clipping: %d -> %d points' %
                            (len(self.scene.get_active_point_cloud().P), len(P)))
        if sys.platform == 'win32':
            self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        else:
            wx.EndBusyCursor()
        self.done_btn.Enable()

    def on_cancel(self, e):
        self.scene.delete_point_cloud('geo_clipping')
        self.scene.get_active_point_cloud().set_visible(True)
        self.Hide()
        self.status_bar.SetStatusText('')

    def on_done(self, e):
        source_pc_name = self.scene.get_active_point_cloud().name
        self.scene.delete_point_cloud(source_pc_name)
        pc = self.scene.get_point_cloud('geo_clipping')
        pc.base_color = 'red'
        new_pc_name = '%s_geoclipped_k=%s_r=%s_d=%s' % \
                         (source_pc_name, self.k_tf.GetValue(),
                          self.r_tf.GetValue(), self.d_tf.GetValue())
        self.scene.update_point_cloud_name(pc.name, new_pc_name)
        pc.reset_colors()
        self.scene.set_active_point_cloud(new_pc_name)
        self.Hide()
