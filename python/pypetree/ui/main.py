import wx, vtk, os.path, datetime
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
from pypetree.ui.world import *
from pypetree.ui.wizards.modified_vl_wizard import *
from pypetree.ui.wizards.lsystem_wizard import *
from pypetree.model.lsystem.lsystem import *
from pypetree.ui.point_cloud import *
from pypetree.ui.model import *


APP_NAME = 'PypeTree'
APP_VERSION = 'prototype'
MAIN_WIN_SIZE = (600, 600) # (400, 400)
MAIN_WIN_BG_COLOR = 'white'#'DarkSlateGray' #'black'
START_WITH_AXES = False #True


class GaugePopup(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, APP_NAME, size=(300, 100))
        self.gauge = wx.Gauge(self, wx.ID_ANY, 100,
                              wx.DefaultPosition, (250, -1))
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.gauge, 0, wx.ALIGN_CENTER_VERTICAL, 10)
        self.SetSizerAndFit(sizer)

    def start_pulse(self, msg):
        self.Bind(wx.EVT_TIMER, self.timer_handler)
        self.timer = wx.Timer(self)
        self.timer.Start(100)
        self.gauge.SetRange(100)
        self.count = 0
        self.SetTitle(msg)
        self.Show()

    def timer_handler(self, event):
        self.count += 1
        self.count %= 100
        self.gauge.Pulse()

    def stop_pulse(self):
        self.timer.Stop()
        self.Hide()


class MainWindow(wx.Frame):

    VIEW_PC_SUBMENU_ID = 100

    def __init__(self, scene):

        wx.Frame.__init__(self, None, wx.ID_ANY, APP_NAME, size=MAIN_WIN_SIZE)
        self.scene = scene

        self.gauge_popup = GaugePopup(self)

        self.iren = wxVTKRenderWindowInteractor(self, -1)
        self.ren = vtk.vtkRenderer()
        self.ren_win = self.iren.GetRenderWindow()
        self.ren_win.AddRenderer(self.ren)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.iren, 1, wx.EXPAND, 0)
        self.SetSizer(sizer)
        self.status_bar = self.CreateStatusBar()

        self.last_mouse_event = None

        # file
        file_menu = wx.Menu()
        open_menuitem = file_menu.Append(wx.ID_OPEN,"&Open",
                                         " Load point cloud, model or markers")
        savemodel_menuitem = file_menu.Append(wx.ID_ANY,"Save Model",
                                              " Save current model")
        self.savecloud_menuitem = file_menu.Append(wx.ID_ANY,
                                                   "Save Point Cloud",
                                                   " Save modified point cloud")
        save_mm_menuitem = file_menu.Append(wx.ID_ANY, "Save Markers",
                                            " Save measurement markers")
        save_ss_menuitem = file_menu.Append(wx.ID_ANY, "Save Screenshot",
                                            " Save screenshot")
        #self.savecloud_menuitem.Enable(False)
        exit_menuitem = file_menu.Append(wx.ID_EXIT,"E&xit",
                                         " Terminate the program")

        # view
        self.view_menu = wx.Menu()

        cloud_submenu = wx.Menu()
        self.view_menu.AppendMenu(MainWindow.VIEW_PC_SUBMENU_ID,
                                  'Point Cloud', cloud_submenu)
        self.select_menuitem = cloud_submenu.AppendCheckItem(wx.ID_ANY,
                                        'Sphere Selection',
                                        ' Enable/disable point cloud selection')
        self.select_menuitem.Check(self.scene.point_cloud_selection_enabled)
        pc_opacity_menuitem = cloud_submenu.Append(wx.ID_ANY, 'Opacity',
                                                ' Adjust point cloud opacity')

        model_submenu = wx.Menu()
        self.volume_menuitem = model_submenu.AppendCheckItem(wx.ID_ANY,
                                            'Volume', ' Show/hide model volume')
        self.volume_menuitem.Check(self.scene.polytube_volume_enabled)
        model_opacity_menuitem = model_submenu.Append(wx.ID_ANY,
                                            'Opacity', ' Adjust model opacity')
        model_tips_mi = model_submenu.AppendCheckItem(wx.ID_ANY,
                                        'Branch Tips', ' Show/hide model tips')
        model_tips_mi.Check(self.scene.polytube_tips_enabled)
        self.view_menu.AppendMenu(wx.ID_ANY, 'Model', model_submenu)

        axes_menuitem = self.view_menu.AppendCheckItem(wx.ID_ANY,
                                            'Axes', ' Show/hide axes')
        axes_menuitem.Check(START_WITH_AXES)

        # point cloud
        pc_menu = wx.Menu()
        clear_pc_menuitem = pc_menu.Append(wx.ID_ANY,
                                           "&Clear"," Clear point cloud")
        pc_aggreg_menuitem = pc_menu.Append(wx.ID_ANY,
                                        'Aggregate', 'Point cloud aggregation')
        #pc_voxel_menuitem = pc_menu.Append(wx.ID_ANY,
        #                      'Voxelize', 'Point cloud voxelization')
        geoclipping_menuitem = pc_menu.Append(wx.ID_ANY,
                        'Geodesic Clipping', 'Geodesic clipping of point cloud')

        # model
        model_menu = wx.Menu()
        clear_model_menuitem = model_menu.Append(wx.ID_ANY,
                                            "&Clear"," Clear current model")
        #smooth_menuitem = model_menu.Append(wx.ID_ANY,
        #                                "&Smooth"," Smooth current model")
        #smooth_menuitem.Enable(False)
        lsys_menuitem = model_menu.Append(wx.ID_ANY,
                                          "&L-System"," Create L-System model")
        add_mm_menuitem = model_menu.Append(wx.ID_ANY,
                           "Add Measurement Markers"," Add measurement markers")
        clear_mm_menuitem = model_menu.Append(wx.ID_ANY,
                   "Clear Measurement Markers"," Clear all measurement markers")

        # reconstruction
        recon_menu = wx.Menu()
        self.mvl_menuitem = recon_menu.Append(wx.ID_ANY,
                                                "Modified Verroust && Lazarus",)
        #self.mvl_menuitem.Enable(False)
        #self.supervised_str_menuitem = recon_menu.Append(wx.ID_ANY, "Lightning",)
        #self.supervised_str_menuitem.Enable(False)

        # help
        help_menu = wx.Menu()
        mouse_nav_menuitem = help_menu.Append(wx.ID_ANY,
                                "Mouse Navigation"," Describe mouse navigation")
        kbd_cmds_menuitem = help_menu.Append(wx.ID_ANY,
                              "Keyboard Commands"," Describe keyboard commands")
        about_menuitem = help_menu.Append(wx.ID_ABOUT,
                                    "&About"," Information about this program")

        menu_bar = wx.MenuBar()
        menu_bar.Append(file_menu, "&File")
        menu_bar.Append(self.view_menu, "&View")
        menu_bar.Append(pc_menu, "&Point Cloud")
        menu_bar.Append(model_menu, "&Model")
        menu_bar.Append(recon_menu, "&Reconstruction")
        menu_bar.Append(help_menu, "&Help")
        #menu_bar.EnableTop(pos=2, enable=False)

        self.SetMenuBar(menu_bar)
        self.Bind(wx.EVT_MENU, self.on_open, open_menuitem)
        self.Bind(wx.EVT_MENU, self.on_save_model, savemodel_menuitem)
        self.Bind(wx.EVT_MENU, self.on_save_pc, self.savecloud_menuitem)
        self.Bind(wx.EVT_MENU, self.on_save_mm, save_mm_menuitem)
        self.Bind(wx.EVT_MENU, self.on_save_screenshot, save_ss_menuitem)
        self.Bind(wx.EVT_MENU, self.on_about, about_menuitem)
        self.Bind(wx.EVT_MENU, lambda e: self.Close(True), exit_menuitem)
        self.Bind(wx.EVT_MENU, lambda e: self.scene.delete_all_point_clouds(),
                  clear_pc_menuitem)
        self.Bind(wx.EVT_MENU, lambda e: self.point_cloud_opacity_dialog.Show(),
                  pc_opacity_menuitem)
        self.Bind(wx.EVT_MENU, self.on_help_mouse_nav, mouse_nav_menuitem)
        self.Bind(wx.EVT_MENU, self.on_help_kbd_commands, kbd_cmds_menuitem)
        self.Bind(wx.EVT_MENU, lambda e: self.scene.delete_model(),
                  clear_model_menuitem)
        self.Bind(wx.EVT_MENU, lambda e:
                  self.scene.set_polytube_volume(
                      self.volume_menuitem.IsChecked()),
                  self.volume_menuitem)
        self.Bind(wx.EVT_MENU, lambda e:
                  self.scene.set_point_cloud_selection(
                      self.select_menuitem.IsChecked()),
                  self.select_menuitem)
        self.Bind(wx.EVT_MENU, self.show_model_opacity_dialog,
                  model_opacity_menuitem)
        self.Bind(wx.EVT_MENU, lambda e: self.mm_dialog.on_show(),
                  add_mm_menuitem)
        self.Bind(wx.EVT_MENU, lambda e:
                  self.scene.clear_measurement_markers(), clear_mm_menuitem)
        self.Bind(wx.EVT_MENU, lambda e: self.mvl_wiz.run(), self.mvl_menuitem)
        #self.Bind(wx.EVT_MENU, lambda e:
        #            self.supervised_str_wiz.run(), self.supervised_str_menuitem)
        self.Bind(wx.EVT_MENU, lambda e: self.lsys_wiz.run(), lsys_menuitem)
        #self.Bind(wx.EVT_MENU, lambda e: None, smooth_menuitem)
        def show_dialog(dlg):
            if self.scene.get_active_point_cloud(): dlg.Show()
            else: self.SetStatusText('A model is required for this!')
        self.Bind(wx.EVT_MENU, lambda e:
                  show_dialog(self.point_cloud_aggregation_dialog),
                  pc_aggreg_menuitem)
        #self.Bind(wx.EVT_MENU, lambda e:
        #       self.point_cloud_voxelization_dialog.Show(), pc_voxel_menuitem)
        self.Bind(wx.EVT_MENU, lambda e:
                  show_dialog(self.point_cloud_geoclipping_dialog),
                  geoclipping_menuitem)

        def set_model_tips_visibility(e):
            self.scene.set_polytube_model_tips_visibility(
                model_tips_mi.IsChecked())
            if model_tips_mi.IsChecked() and \
              self.scene.get_active_polytube_model():
                self.SetStatusText("%d tips" %
                  self.scene.get_active_polytube_model().K.get_number_of_tips())

        self.Bind(wx.EVT_MENU, set_model_tips_visibility, model_tips_mi)
        #lambda e: self.scene.set_polytube_model_tips_visibility(
        #                          model_tips_mi.IsChecked()), model_tips_mi)

        def set_axes_visibility(e):
            self.axes_actor.SetVisibility(axes_menuitem.IsChecked())
            self.ren_win.Render()

        self.Bind(wx.EVT_MENU, set_axes_visibility, axes_menuitem)
        self.Bind(wx.EVT_CLOSE, lambda e: sys.exit(0))

        # MVL wizard
        self.mvl_wiz = MVLWizard(self,
                                'Modified Verroust & Lazarus Reconstruction', 4)
        self.mvl_wiz.add_page(MVLGeodesicConnectivityWizardPage(self.mvl_wiz))
        self.mvl_wiz.add_page(MVLLevelSetWizardPage(self.mvl_wiz))
        self.mvl_wiz.add_page(MVLReconstructionWizardPage(self.mvl_wiz))
        self.mvl_wiz.add_page(MVLSmoothingWizardPage(self.mvl_wiz))

        self.point_cloud_opacity_dialog = PointCloudOpacityDialog(self)
        self.point_cloud_aggregation_dialog = PointCloudAggregationDialog(self)
        self.point_cloud_voxelization_dialog = PointCloudVoxelizationDialog(self)
        self.point_cloud_geoclipping_dialog = PointCloudGeoClippingDialog(self)

        self.model_opacity_dialog = ModelOpacityDialog(self)
        self.mm_dialog = MeasurementMarkersDialog(self)

        # Lsys wizard
        self.lsys_wiz = LSystemWizard(self, 'L-System', 2)
        self.lsys_wiz.add_page(LSystemStructureWizardPage(self.lsys_wiz))
        self.lsys_wiz.add_page(LSystemSamplingWizardPage(self.lsys_wiz))

        self.Layout()
        self.Show(True)

    def show_model_opacity_dialog(self, e=None, value_update=None):
        if value_update:
            self.scene.get_active_polytube_model().\
                actor.GetProperty().SetOpacity(0.75)
            self.model_opacity_dialog.update_slider()
        self.model_opacity_dialog.Show()

    def on_open(self, e):
        dlg = wx.FileDialog(self, "Choose a file", '../data', '',
              "Point cloud files (*.asc)|*.asc|Model/marker files (*.csv)|*.csv",
              wx.OPEN)
        #dlg = wx.FileDialog(self, "Choose a file", '../data', '',
        #      "Model files (*.csv)|*.csv|Point cloud files (*.asc)|*.asc",
        #      wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            if sys.platform == 'win32':
                self.SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
            else:
                wx.BeginBusyCursor()
            wx.Yield()
            #self.gauge_popup.start_pulse('Loading..')
            fn = os.path.join(dlg.GetDirectory(), dlg.GetFilename())
            self.SetStatusText("Loading %s.." % dlg.GetFilename())
            if fn.endswith('.asc'):
                self.scene.load_point_cloud(fn)
                #self.gauge_popup.stop_pulse()
                self.SetTitle('%s - %s' % (APP_NAME, dlg.GetFilename()))
                #self.auto_menuitem.Enable()
                #self.mvl_menuitem.Enable()
                #self.supervised_str_menuitem.Enable()
                self.view_menu.Enable(MainWindow.VIEW_PC_SUBMENU_ID, True)
                self.GetMenuBar().EnableTop(pos=2, enable=True)
                self.SetStatusText("%d points in cloud" %
                                   len(self.scene.get_active_point_cloud().P))
            elif fn.endswith('.csv'):
                if self.scene.load_model_or_markers(fn) == 'model':
                    K = self.scene.get_active_polytube_model().K
                    dims = K.get_dimensions()
                    st = '%d tips, %d levels (dims: %0.2f x %0.2f x ' \
                         '%0.2f, surf: %0.2f)' % (K.get_number_of_tips(),
                                                  K.get_number_of_levels(),
                                                  dims[0], dims[1], dims[2],
                                                  K.get_surface())
                    self.SetStatusText(st)
            else: raise Exception('unknown file extension')
            if sys.platform == 'win32':
                self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
            else:
                wx.EndBusyCursor()
        dlg.Destroy()

    def on_save_model(self, e):
        if not self.scene.get_active_polytube_model():
            self.SetStatusText('A model is required for this!')
            return
        fn = '%s.csv' % self.scene.get_active_polytube_model().name
        dlg = wx.FileDialog(self, "Choose a file", '', fn,
                            "Model file (*.csv)|*.csv",
                            wx.SAVE | wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            fn = os.path.join(dlg.GetDirectory(), dlg.GetFilename())
            ffn = dlg.GetFilename()
            if not fn.endswith('.csv'):
                fn += '.csv'
                ffn += '.csv'
            self.scene.save_model(fn)
            self.SetStatusText("Saved %s" % ffn)
        dlg.Destroy()

    def on_save_pc(self, e):
        if not self.scene.get_active_point_cloud():
            self.SetStatusText('A point cloud is required for this!')
            return
        fn = '%s.asc' % self.scene.get_active_point_cloud().name
        dlg = wx.FileDialog(self, "Choose a file", '', fn,
                            "Point cloud file (*.asc)|*.asc",
                            wx.SAVE | wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            fn = os.path.join(dlg.GetDirectory(), dlg.GetFilename())
            ffn = dlg.GetFilename()
            if not fn.endswith('.asc'):
                fn += '.asc'
                ffn += '.asc'
            self.scene.save_point_cloud(fn)
            self.SetStatusText("Saved %s" % ffn)
        dlg.Destroy()

    def on_save_mm(self, e):
        mms = self.scene.get_measurement_markers()
        if not self.scene.get_measurement_markers():
            self.SetStatusText('No measurement markers found')
            return
        fn = '%s_markers=%d.csv' % \
              (self.scene.get_active_polytube_model().name, len(mms))
        dlg = wx.FileDialog(self, "Choose a file", '', fn,
                            "Marker file (*.csv)|*.csv",
                            wx.SAVE | wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            fn = os.path.join(dlg.GetDirectory(), dlg.GetFilename())
            ffn = dlg.GetFilename()
            if not fn.endswith('.csv'):
                fn += '.csv'
                ffn += '.csv'
            self.scene.save_measurement_markers(fn)
            self.SetStatusText("Saved %s" % ffn)
        dlg.Destroy()

    def on_save_screenshot(self, e):
        fn = 'PypeTree_screenshot_%s.tiff' % datetime.datetime.now().isoformat()
        dlg = wx.FileDialog(self, "Choose a file", '', fn,
              "TIFF file (*.tiff)|*.tiff|EPS file (*.eps)|*.eps|" \
             "PNG file (*.png)|*.png|JPG file (*.jpg)|*.jpg",
             wx.SAVE | wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            #fn, ext = os.path.splitext(os.path.join(dlg.GetDirectory(),
            #                                        dlg.GetFilename()))
            fn = os.path.join(dlg.GetDirectory(), dlg.GetFilename())
            #if ext.lower() not in ['.eps', '.png', '.tiff', '.jpg']:
            #    self.SetStatusText('Can only save screenshots' \
            #                       'in .tiff, .eps or .png')
            #    return
            self.scene.save_screenshot(fn, '.eps')
            self.scene.save_screenshot(fn, '.tiff')
            self.scene.save_screenshot(fn, '.png')
            self.scene.save_screenshot(fn, '.jpg')
            self.SetStatusText("Saved %s" % dlg.GetFilename())
        dlg.Destroy()

    def on_about(self, e):
        s = '%s (%s)\nCreated by Christian Jauvin' % (APP_NAME, APP_VERSION)
        dlg = wx.MessageDialog(self, s, "About", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def on_help_kbd_commands(self, e):
        s = """
k (with pointer on point cloud): add an articulation sphere

s (with pointer on sphere): select sphere

c (with pointer on model): connect selected sphere to model

d: delete selected sphere (will not affect model)

D: (while sphere is selected): delete selected points inside sphere

x: cut model branch above selected sphere

X: cut model branch from nearest down branching point

f: center camera (fly-to) on point

r: reset view
"""
        dlg = wx.MessageDialog(self, s, 'Keyboard Commands', wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def on_help_mouse_nav(self, e):
        s = """
left button: rotate camera, or move sphere

middle button: pan camera, or move sphere

right button (drag up/down): zoom camera, or scale sphere

wheel: zoom camera

left double-click: add an articulation sphere (roaming or attached to model), or center camera on existing one (and select it)
"""
        dlg = wx.MessageDialog(self, s, 'Mouse Navigation', wx.OK)
        dlg.ShowModal()
        dlg.Destroy()


class SceneInterface:

    def __init__(self):

        self.scene = Scene()
        self.frame = MainWindow(self.scene)

        self.camera_style = vtk.vtkInteractorStyleTrackballCamera()
        self.camera_style.AddObserver('LeftButtonPressEvent',
                                      self.bimodal_mouse_handler)
        self.camera_style.AddObserver('LeftButtonReleaseEvent',
                                      self.bimodal_mouse_handler)
        self.camera_style.AddObserver('MiddleButtonPressEvent',
                                      self.bimodal_mouse_handler)
        self.camera_style.AddObserver('MiddleButtonReleaseEvent',
                                      self.bimodal_mouse_handler)
        self.camera_style.AddObserver('RightButtonPressEvent',
                                      self.bimodal_mouse_handler)
        self.camera_style.AddObserver('RightButtonReleaseEvent',
                                      self.bimodal_mouse_handler)
        self.camera_style.AddObserver('MouseWheelForwardEvent',
                                      self.bimodal_mouse_handler)
        self.camera_style.AddObserver('MouseWheelBackwardEvent',
                                      self.bimodal_mouse_handler)
        self.camera_style.AddObserver('KeyPressEvent', lambda a, b: None)

        self.actor_style = vtk.vtkInteractorStyleTrackballActor()
        self.actor_style.AddObserver('LeftButtonPressEvent',
                                     self.bimodal_mouse_handler)
        self.actor_style.AddObserver('LeftButtonReleaseEvent',
                                     self.bimodal_mouse_handler)
        self.actor_style.AddObserver('MiddleButtonPressEvent',
                                     self.bimodal_mouse_handler)
        self.actor_style.AddObserver('MiddleButtonReleaseEvent',
                                     self.bimodal_mouse_handler)
        self.actor_style.AddObserver('RightButtonPressEvent',
                                     self.bimodal_mouse_handler)
        self.actor_style.AddObserver('RightButtonReleaseEvent',
                                     self.bimodal_mouse_handler)
        self.actor_style.AddObserver('MouseWheelForwardEvent',
                                     self.bimodal_mouse_handler)
        self.actor_style.AddObserver('MouseWheelBackwardEvent',
                                     self.bimodal_mouse_handler)
        self.actor_style.AddObserver('KeyPressEvent', lambda a, b: None)

        self.frame.iren.SetInteractorStyle(self.camera_style)
        self.frame.iren.AddObserver('KeyPressEvent', self.keypress_handler)
        self.frame.ren.SetBackground(name_to_rgb_float(MAIN_WIN_BG_COLOR))
        self.scene.frame = self.frame

        axes = vtk.vtkAxes()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(axes.GetOutputPort())
        self.frame.axes_actor = vtk.vtkActor()
        self.frame.axes_actor.SetMapper(mapper)
        self.frame.axes_actor.GetProperty().SetLineWidth(1)
        self.frame.axes_actor.SetVisibility(START_WITH_AXES)
        self.frame.ren.AddActor(self.frame.axes_actor)

    def bimodal_mouse_handler(self, obj, event):

        # mouse wheel: camera mode only

        if event.endswith('PressEvent'):
            wx.SetCursor(wx.StockCursor(wx.CURSOR_SIZING))
        elif event.endswith('ReleaseEvent'):
            wx.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

        if event.startswith('MouseWheel'):
            self.frame.iren.SetInteractorStyle(self.camera_style)
            if event == 'MouseWheelForwardEvent':
                self.camera_style.OnMouseWheelForward()
            else: self.camera_style.OnMouseWheelBackward()
            return

        # detect double-click
        is_dbl_click = (event == 'LeftButtonReleaseEvent' and
                        self.frame.last_mouse_event == 'LeftButtonReleaseEvent')
        self.frame.last_mouse_event = event

        if is_dbl_click:

            pos2d = self.frame.iren.GetEventPosition()
            picker = vtk.vtkPropPicker()
            if picker.PickProp(pos2d[0], pos2d[1], self.frame.ren):
                # picked already existing sphere: select and fly-to
                if picker.GetActor() in self.scene.actor_to_sphere:
                    picked_sphere = self.scene.actor_to_sphere[picker.GetActor()]
                    self.scene.unselect_all_articulation_spheres()
                    picked_sphere.set_selected(True)
                    self.frame.iren.FlyTo(self.frame.ren,
                                          *picked_sphere.get_position())
                # add polytube articulation
                elif self.scene.get_active_polytube_model() and \
                  picker.GetActor() is \
                            self.scene.get_active_polytube_model().actor:
                    m = self.scene.get_active_polytube_model()
                    m.add_articulation_sphere_to_closest_point(pos2d)
            else:
                self.scene.add_articulation_sphere(pos2d)
            return

        # try to pick a sphere
        picker = vtk.vtkPropPicker()
        pos2d = self.frame.iren.GetEventPosition()
        if picker.PickProp(pos2d[0], pos2d[1], self.frame.ren):
            if picker.GetActor() in self.scene.actor_to_sphere and \
                   self.scene.actor_to_sphere[picker.GetActor()].is_selected:
                self.scene.picked_sphere_actor = picker.GetActor()

        # camera mode
        if not self.scene.picked_sphere_actor:

            # make sure it's reset when picked_non_movable_sphere
            self.scene.picked_sphere_actor = None
            self.frame.iren.SetInteractorStyle(self.camera_style)
            if event == 'LeftButtonPressEvent':
                self.camera_style.OnLeftButtonDown()
            elif event == 'LeftButtonReleaseEvent':
                self.camera_style.OnLeftButtonUp()
            elif event == 'MiddleButtonPressEvent':
                self.camera_style.OnMiddleButtonDown()
            elif event == 'MiddleButtonReleaseEvent':
                self.camera_style.OnMiddleButtonUp()
            elif event == 'RightButtonPressEvent':
                self.camera_style.OnRightButtonDown()
            elif event == 'RightButtonReleaseEvent':
                self.camera_style.OnRightButtonUp()

        # actor mode
        else:

            self.frame.iren.SetInteractorStyle(self.actor_style)
            psa = self.scene.picked_sphere_actor
            picked_sphere = self.scene.actor_to_sphere[psa]

            if event.endswith('ButtonReleaseEvent'):
                picked_sphere.update()
                picked_sphere.run_callbacks('moved')
                self.scene.picked_sphere_actor = None
            if event in ['LeftButtonPressEvent', 'MiddleButtonPressEvent']:
                self.actor_style.OnMiddleButtonDown()
            elif event in ['LeftButtonReleaseEvent', 'MiddleButtonReleaseEvent']:
                self.actor_style.OnMiddleButtonUp()
            elif event == 'RightButtonPressEvent':
                self.actor_style.OnRightButtonDown()
            elif event == 'RightButtonReleaseEvent':
                self.actor_style.OnRightButtonUp()

    def keypress_handler(self, obj, event):

        key = obj.GetKeyCode()
        pos2d = obj.GetEventPosition()

        # create new sphere
        if key == "k":

            self.scene.add_articulation_sphere(pos2d)

        # mark sphere for connection if no other marker set, connect otherwise
        elif key == "c":

            selected_sphere = None # there should be at most 1
            for sphere in self.scene.actor_to_sphere.values():
                if sphere.is_selected:
                    selected_sphere = sphere
                    break
            if not selected_sphere: return
            picker = vtk.vtkPropPicker()
            if picker.PickProp(pos2d[0], pos2d[1], self.frame.ren):
                actor = picker.GetActor()
                if self.scene.get_active_polytube_model() and \
                  actor is self.scene.get_active_polytube_model().actor:
                    m = self.scene.get_active_polytube_model()
                    m.connect_articulation_sphere_to_closest_point(
                                                        selected_sphere, pos2d)

        # select sphere (only one at a time)
        elif key == "s":

            for sphere in self.scene.actor_to_sphere.values():
                sphere.set_selected(False)

            picker = vtk.vtkPropPicker()
            if picker.PickProp(pos2d[0], pos2d[1], self.frame.ren):
                actor = picker.GetActor()
                if actor in self.scene.actor_to_sphere:
                    self.scene.actor_to_sphere[actor].toggle_selected()

        # delete selected sphere
        elif key == "d":

            for sphere in self.scene.actor_to_sphere.values():
                if sphere.is_selected:
                    self.scene.delete_articulation_sphere(sphere)
                    sphere.run_callbacks('delete')

        elif key == 'D':

            for sphere in self.scene.actor_to_sphere.values():
                if sphere.is_selected:
                    n = sphere.delete_selected_points()
                    self.frame.SetStatusText('Deleted %d points' % n)
                    wiz = self.frame.mvl_wiz
                    if wiz.model is not None and wiz.curr_page == wiz.pages[0]:
                        wiz.model.P = self.scene.get_active_point_cloud().P
                        wiz.curr_page.on_run(None)

        # cut polytube model node
        elif key in 'xX':

            for sphere in self.scene.actor_to_sphere.values():
                if sphere.is_selected:
                    if key == 'x':
                        sphere.run_callbacks('cut_above')
                    else:
                        sphere.run_callbacks('cut_branch')

        # fly-to (set camera focal point)
        elif key == "f":

            if self.scene.get_active_point_cloud():
                self.scene.get_active_point_cloud().actor.SetPickable(True)
                picker = vtk.vtkPointPicker()
                if picker.Pick(pos2d[0], pos2d[1], 0, self.frame.ren):
                    self.frame.iren.FlyTo(self.frame.ren,
                                          *picker.GetPickPosition())
                self.scene.get_active_point_cloud().actor.SetPickable(False)

        elif key == 'N':

            for sphere in self.scene.actor_to_sphere.values():
                if sphere.is_selected:
                    wiz = self.frame.mvl_wiz
                    if wiz.model is not None and wiz.curr_page == wiz.pages[0]:
                        sphere.stitch_neighborhood_graph(wiz.model.N_full)
                        wiz.model.find_nn_connected_components()
                        n_comps, n_nodes_biggest, density = \
                                            wiz.model.get_connectivity_infos()
                        self.scene.set_point_cloud_graph(wiz.model.N_full)
                        wiz.pages[0].set_nn_connected_components_color_scheme(
                                                         wiz.model.N_components)
                        wiz.pages[1].is_dirty = True
                        st = 'Found %s connected component%s (biggest has ' \
                             '%s nodes; conn. factor = %f)' % \
                             (n_comps, 's' if n_comps>1 else '',
                              n_nodes_biggest, density)
                        self.frame.SetStatusText(st)

        # # contract sphere (not used, buggy)
        # elif key == "C":

        #     picker = vtk.vtkPropPicker()
        #     if picker.PickProp(pos2d[0], pos2d[1], self.frame.ren):
        #         actor = picker.GetActor()
        #         self.scene.actor_to_sphere[actor].contract()

app = wx.PySimpleApp()
SceneInterface()
app.MainLoop()
