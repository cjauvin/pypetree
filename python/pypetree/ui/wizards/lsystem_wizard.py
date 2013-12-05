from pypetree.model.lsystem.lsystem import *
from pypetree.ui.wizards.wizard import *
from pypetree.ui.world import *

class LSystemWizard(Wizard):

    def on_finish(self, e):
        self.parent.scene.get_point_cloud('lsys').base_color = 'red'
        self.parent.scene.get_point_cloud('lsys').reset_colors()
        p0 = self.pages[0]
        p1 = self.pages[1]
        new_model_name = \
            'a=%s_r="%s"_n=%s_am=%s_asd=%s_isl=%s_isr=%s_sls=%s_srs=%s' % \
            (p0.axiom_tf.GetValue(), p0.rule_tf.GetValue(),
             p0.niters_tf.GetValue(), p0.angle_tf.GetValue(),
             p0.angle_sd_tf.GetValue(), p0.init_seglen_tf.GetValue(),
             p0.init_segrad_tf.GetValue(), p0.seglen_scaling_tf.GetValue(),
             p0.segrad_scaling_tf.GetValue())
        if p0.seed_tf.GetValue().strip():
            new_model_name += '_sts=%s' % p0.seed_tf.GetValue().strip()
        new_pc_name = '%s_d=%s_dev=%s' % (new_model_name,
                                          p1.density_tf.GetValue(),
                                          p1.deviation_tf.GetValue())
        if p1.seed_tf.GetValue().strip():
            new_pc_name += '_sas=%s' % p1.seed_tf.GetValue().strip()
        self.parent.scene.update_polytube_model_name('lsys', new_model_name)
        self.parent.scene.update_point_cloud_name('lsys', new_pc_name)
        self.curr_page.Hide()
        self.Hide()

class LSystemStructureWizardPage(WizardPage):

    def __init__(self, wiz):

        WizardPage.__init__(self, wiz, 'Structure (Step 1/2)')
        size = (200,-1)
        axiom_lbl = wx.StaticText(self, wx.ID_ANY, 'Axiom:', size=size)
        self.axiom_tf = wx.TextCtrl(self, wx.ID_ANY, 'FA')
        axiom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        axiom_sizer.Add(axiom_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        axiom_sizer.Add(self.axiom_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        rule_lbl = wx.StaticText(self, wx.ID_ANY, 'Rules:', size=size)
        #self.rule_tf = wx.TextCtrl(self, wx.ID_ANY, 'A->[^FA][vFA][<FA][>FA]',
        #                           style=wx.TE_MULTILINE, size=size)
        self.rule_tf = wx.TextCtrl(self, wx.ID_ANY, 'A->[^FA]+++[>FA]',
                                   style=wx.TE_MULTILINE, size=size)
        rule_sizer = wx.BoxSizer(wx.HORIZONTAL)
        rule_sizer.Add(rule_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        rule_sizer.Add(self.rule_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        niters_lbl = wx.StaticText(self, wx.ID_ANY,
                                   'Number of iterations:', size=size)
        self.niters_tf = wx.TextCtrl(self, wx.ID_ANY, '6')
        niters_sizer = wx.BoxSizer(wx.HORIZONTAL)
        niters_sizer.Add(niters_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        niters_sizer.Add(self.niters_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        angle_lbl = wx.StaticText(self, wx.ID_ANY,
                                  'Angle mean (in degrees):', size=size)
        self.angle_tf = wx.TextCtrl(self, wx.ID_ANY, '30')
        angle_sizer = wx.BoxSizer(wx.HORIZONTAL)
        angle_sizer.Add(angle_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        angle_sizer.Add(self.angle_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        angle_sd_lbl = wx.StaticText(self, wx.ID_ANY,
                                     'Angle std dev (in degrees):', size=size)
        self.angle_sd_tf = wx.TextCtrl(self, wx.ID_ANY, '5')
        angle_sd_sizer = wx.BoxSizer(wx.HORIZONTAL)
        angle_sd_sizer.Add(angle_sd_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        angle_sd_sizer.Add(self.angle_sd_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        init_seglen_lbl = wx.StaticText(self, wx.ID_ANY,
                                        'Initial segment length:', size=size)
        self.init_seglen_tf = wx.TextCtrl(self, wx.ID_ANY, '1')
        init_seglen_sizer = wx.BoxSizer(wx.HORIZONTAL)
        init_seglen_sizer.Add(init_seglen_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        init_seglen_sizer.Add(self.init_seglen_tf, 0,
                              wx.ALIGN_CENTER_VERTICAL, 10)
        init_segrad_lbl = wx.StaticText(self, wx.ID_ANY,
                                        'Initial segment radius:', size=size)
        self.init_segrad_tf = wx.TextCtrl(self, wx.ID_ANY, '0.1')
        init_segrad_sizer = wx.BoxSizer(wx.HORIZONTAL)
        init_segrad_sizer.Add(init_segrad_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        init_segrad_sizer.Add(self.init_segrad_tf, 0,
                              wx.ALIGN_CENTER_VERTICAL, 10)
        seglen_scaling_lbl = wx.StaticText(self, wx.ID_ANY,
                                           'Segment length scaling:', size=size)
        self.seglen_scaling_tf = wx.TextCtrl(self, wx.ID_ANY, '0.75')
        seglen_scaling_sizer = wx.BoxSizer(wx.HORIZONTAL)
        seglen_scaling_sizer.Add(seglen_scaling_lbl, 0,
                                 wx.ALIGN_CENTER_VERTICAL, 10)
        seglen_scaling_sizer.Add(self.seglen_scaling_tf, 0,
                                 wx.ALIGN_CENTER_VERTICAL, 10)
        segrad_scaling_lbl = wx.StaticText(self, wx.ID_ANY,
                                           'Segment radius scaling:', size=size)
        self.segrad_scaling_tf = wx.TextCtrl(self, wx.ID_ANY, '0.75')
        segrad_scaling_sizer = wx.BoxSizer(wx.HORIZONTAL)
        segrad_scaling_sizer.Add(segrad_scaling_lbl, 0,
                                 wx.ALIGN_CENTER_VERTICAL, 10)
        segrad_scaling_sizer.Add(self.segrad_scaling_tf, 0,
                                 wx.ALIGN_CENTER_VERTICAL, 10)
        seed_lbl = wx.StaticText(self, wx.ID_ANY, 'Random seed:', size=size)
        self.seed_tf = wx.TextCtrl(self, wx.ID_ANY, '')
        seed_sizer = wx.BoxSizer(wx.HORIZONTAL)
        seed_sizer.Add(seed_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        seed_sizer.Add(self.seed_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        self.sizer.Add(axiom_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(rule_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(niters_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(angle_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(angle_sd_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(init_seglen_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(init_segrad_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(seglen_scaling_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(segrad_scaling_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(seed_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.SetSizerAndFit(self.sizer)

    def on_run(self, e):
        wx.BeginBusyCursor()
        wx.SafeYield()
        self.status_bar.SetStatusText('')

        sls = self.seglen_scaling_tf.GetValue().split()
        srs = self.segrad_scaling_tf.GetValue().split()
        self.wiz.model = LSystemTree(axiom=self.axiom_tf.GetValue(),
            rules=dict([r.split('->')
                        for r in self.rule_tf.GetValue().split()]),
                        n_iters=int(self.niters_tf.GetValue()),
                        angle_mean_in_degrees=float(self.angle_tf.GetValue()),
                        angle_sd_in_degrees=float(self.angle_sd_tf.GetValue()),
                        init_seglen=float(self.init_seglen_tf.GetValue()),
                        init_segrad=float(self.init_segrad_tf.GetValue()),
                        seglen_scaling=float(sls[0]),
                        seglen_scaling_sd=float(sls[1] if len(sls) > 1 else 0.0),
                        segrad_scaling=float(srs[0]),
                        segrad_scaling_sd=float(srs[1] if len(srs) > 1 else 0.0),
                        seed=self.seed_tf.GetValue().strip())
        self.scene.add_polytube_model(self.wiz.model.K, 'lsys')
        self.scene.frame.ren.ResetCamera()
        wx.EndBusyCursor()
        dims = self.wiz.model.K.get_dimensions()
        st = '%d tips, %d levels (dims: %0.2f x %0.2f x %0.2f, surf: %0.2f)' % \
             (self.wiz.model.K.get_number_of_tips(),
              self.wiz.model.K.get_number_of_levels(),
              dims[0], dims[1], dims[2],
              self.wiz.model.K.get_surface())
        self.status_bar.SetStatusText(st)
        self.wiz.nav_pnl.next_btn.Enable(True)
        self.is_dirty = False
        self.next.is_dirty = True

    def on_enter(self, e):
        self.update_nav_buttons_and_show()
        if not self.is_dirty:
            self.scene.set_polytube_model_visibility('lsys', True)

    def on_leave(self, e):
        self.scene.set_polytube_model_visibility('lsys', False)
        self.Hide()

class LSystemSamplingWizardPage(WizardPage):

    def __init__(self, wiz):

        WizardPage.__init__(self, wiz, 'Sampling (Step 2/2)')
        size = (200,-1)
        density_lbl = wx.StaticText(self, wx.ID_ANY, 'Density:', size=size)
        self.density_tf = wx.TextCtrl(self, wx.ID_ANY, '2500')
        density_sizer = wx.BoxSizer(wx.HORIZONTAL)
        density_sizer.Add(density_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        density_sizer.Add(self.density_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        deviation_lbl = wx.StaticText(self, wx.ID_ANY, 'Deviation:', size=size)
        self.deviation_tf = wx.TextCtrl(self, wx.ID_ANY, '0.001')
        deviation_sizer = wx.BoxSizer(wx.HORIZONTAL)
        deviation_sizer.Add(deviation_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        deviation_sizer.Add(self.deviation_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        seed_lbl = wx.StaticText(self, wx.ID_ANY, 'Random seed:', size=size)
        self.seed_tf = wx.TextCtrl(self, wx.ID_ANY, '')
        seed_sizer = wx.BoxSizer(wx.HORIZONTAL)
        seed_sizer.Add(seed_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        seed_sizer.Add(self.seed_tf, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        self.show_model_cb = wx.CheckBox(self, wx.ID_ANY, 'Show Model')
        self.show_model_cb.SetValue(True)
        sm_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sm_sizer.Add(self.show_model_cb, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        wx.EVT_CHECKBOX(self, self.show_model_cb.GetId(),
                    lambda e: self.scene.set_polytube_model_visibility('default',
                                                self.show_model_cb.GetValue()))
        self.sizer.Add(density_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(deviation_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(seed_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.sizer.Add(sm_sizer, 0, wx.ALL|wx.EXPAND, 10)
        self.SetSizerAndFit(self.sizer)

    def on_run(self, e):
        wx.BeginBusyCursor()
        wx.SafeYield()
        self.status_bar.SetStatusText('Sampling L-System model..')
        self.scene.set_polytube_model_visibility('lsys',
                                              self.show_model_cb.GetValue())
        self.wiz.model.sample(density=int(self.density_tf.GetValue()),
                              deviation=float(self.deviation_tf.GetValue()),
                              add_source_point=True,
                              seed=self.seed_tf.GetValue().strip())
        self.scene.add_point_cloud(self.wiz.model.P, 'lsys', 'limegreen')
        wx.EndBusyCursor()
        self.status_bar.SetStatusText('%s points' % len(self.wiz.model.P))
        self.wiz.nav_pnl.next_btn.Enable(True)
        self.is_dirty = False

    def on_enter(self, e):
        self.update_nav_buttons_and_show()
        self.scene.set_polytube_model_visibility('lsys',
                                              self.show_model_cb.GetValue())
        if not self.is_dirty:
            self.scene.set_point_cloud_visibility('lsys', True)

    def on_leave(self, e):
        self.scene.set_polytube_model_visibility('lsys', False)
        self.scene.set_point_cloud_visibility('lsys', False)
        self.Hide()
