import wx

class ModelOpacityDialog(wx.Dialog):

    def __init__(self, parent):

        def set_opacity(e):
            if self.scene.get_active_polytube_model():
                self.scene.get_active_polytube_model().actor.GetProperty().\
                     SetOpacity(self.slider.GetValue() / 100.0)
            if self.scene.get_active_voxel_model():
                self.scene.get_active_voxel_model().actor.GetProperty().\
                     SetOpacity(self.slider.GetValue() / 100.0)
            self.scene.frame.ren_win.Render()

        self.parent = parent
        wx.Dialog.__init__(self, self.parent, wx.ID_ANY, 'Model Opacity')
        self.scene = self.parent.scene
        self.slider = wx.Slider(self, wx.ID_ANY, 100, 0, 100,
                            wx.DefaultPosition, (250, -1),
                            wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.Bind(wx.EVT_SLIDER, set_opacity)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.slider, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        self.SetSizerAndFit(sizer)

    def update_slider(self):
        self.slider.SetValue(self.scene.get_active_polytube_model().\
                             actor.GetProperty().GetOpacity() * 100)

class MeasurementMarkersDialog(wx.Dialog):

    def __init__(self, parent):

        wx.Dialog.__init__(self, parent, wx.ID_ANY, 'Measurement Markers')

        self.parent = parent
        self.scene = self.parent.scene
        self.status_bar = self.parent.status_bar

        n_lbl = wx.StaticText(self, wx.ID_ANY,
            'Number of markers (including the two user-defined, green ones):',
            size=(250,-1))
        self.n_tf = wx.TextCtrl(self, wx.ID_ANY, '5')
        n_sizer = wx.BoxSizer(wx.HORIZONTAL)
        n_sizer.Add(n_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        n_sizer.Add(self.n_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)

        run_btn = wx.Button(self, wx.ID_ANY, 'Run')
        cancel_btn = wx.Button(self, wx.ID_ANY, 'Cancel')
        self.done_btn = wx.Button(self, wx.ID_ANY, 'Done')
        #self.done_btn.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.on_run, run_btn)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, cancel_btn)
        self.Bind(wx.EVT_BUTTON, self.on_done, self.done_btn)
        self.Bind(wx.EVT_CLOSE, lambda e: self.on_cancel(e))
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(run_btn, 0, wx.ALL|wx.EXPAND, 10)
        btn_sizer.Add(cancel_btn, 0, wx.ALL|wx.EXPAND, 10)
        btn_sizer.Add(self.done_btn, 0, wx.ALL|wx.EXPAND, 10)

        top_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer.Add(n_sizer, 0, wx.ALL|wx.EXPAND, 10)
        top_sizer.Add(btn_sizer, 0, wx.ALL|wx.ALIGN_RIGHT, 10)

        self.SetSizerAndFit(top_sizer)

    def on_show(self):
        if not self.scene.get_active_polytube_model():
            self.status_bar.SetStatusText('Error: a model is required for this!')
            return
        #self.parent.show_model_opacity_dialog(value_update=0.75)
        self.initial_volume_menuitem_state = self.scene.polytube_volume_enabled
        self.scene.set_polytube_volume(False)
        self.parent.volume_menuitem.Check(False)
        self.scene.get_active_polytube_model().add_user_measurement_markers()
        self.Show()

    def on_run(self, e):
        if not self.scene.get_active_polytube_model().\
          find_interpolated_measurement_markers(int(self.n_tf.GetValue())):
            self.status_bar.SetStatusText("Error: it's not possible to derive " \
                                "a branch segment from the two green markers")

    def on_cancel(self, e):
        self.scene.get_active_polytube_model().clear_current_measurement_markers()
        self.scene.set_polytube_volume(self.initial_volume_menuitem_state)
        self.parent.volume_menuitem.Check(self.initial_volume_menuitem_state)
        self.Hide()

    def on_done(self, e):
        self.scene.get_active_polytube_model().commit_current_measurement_markers()
        self.scene.set_polytube_volume(self.initial_volume_menuitem_state)
        self.parent.volume_menuitem.Check(self.initial_volume_menuitem_state)
        self.Hide()
