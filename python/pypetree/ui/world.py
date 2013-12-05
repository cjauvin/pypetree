from __future__ import division
import vtk, wx, argparse, json, cPickle, os.path, re
from numpy import *
from collections import defaultdict
from pypetree.model.point_cloud import *
from pypetree.model.tree_model import *

INIT_SPHERE_RADIUS = 0.05
ART_SPHERE_SIZE_RATIO = 1.25

# container for both the point cloud and the model
class Scene:

    def __init__(self):
        self.point_clouds = {} # name to PointCloud
        self.active_point_cloud = None
        self.polytube_models = {} # name to PolytubeModel
        self.active_polytube_model = None
        self.voxel_models = {} # name to VoxelModel
        self.active_voxel_model = None
        self.actor_to_sphere = {}
        self.picked_sphere_actor = None
        self.polytube_volume_enabled = True
        self.point_cloud_selection_enabled = True
        self.polytube_tips_enabled = False
        # will be set later at the end of SceneInterface.__init__
        self.frame = None

    def delete_all_point_clouds(self):
        for pc in self.point_clouds.values():
            pc.delete()
        self.point_clouds = {}

    def delete_point_cloud(self, pc_name):
        if pc_name not in self.point_clouds: return
        self.point_clouds[pc_name].delete()
        del self.point_clouds[pc_name]
        if pc_name == self.active_point_cloud:
            self.active_point_cloud = None

    def delete_model(self):
        for ptm in self.polytube_models.values():
            ptm.delete()
        for sphere in self.actor_to_sphere.values():
            sphere.delete()
        self.actor_to_sphere = {}
        for vm in self.voxel_models.values():
            vm.delete()
        self.polytube_models = {}
        self.frame.ren_win.Render()

    def delete_all(self):
        self.delete_all_point_clouds()
        self.delete_model()

    def save_model(self, fn):
        self.get_active_polytube_model().K.save(fn)

    def save_point_cloud(self, fn):
        savetxt(fn, self.get_active_point_cloud().P)

    def load_point_cloud(self, fn):
        self.delete_all_point_clouds()
        cols = [0,1,2]
        up = None
        m = re.search('up=(\d)', fn)
        if m:
            up = int(m.group(1))
            if up in [0,1,2]:
                cols.remove(up)
                cols.insert(1, up)
        self.add_point_cloud(loadtxt(fn, usecols=cols),
                           os.path.splitext(os.path.basename(fn))[0], up=up)

    def get_active_point_cloud(self):
        return self.point_clouds.get(self.active_point_cloud)

    def update_point_cloud_name(self, pc_name, new_pc_name):
        self.point_clouds[new_pc_name] = self.point_clouds[pc_name]
        self.point_clouds[new_pc_name].name = new_pc_name
        del self.point_clouds[pc_name]
        if self.active_point_cloud == pc_name:
            self.active_point_cloud = new_pc_name

    def update_polytube_model_name(self, model_name, new_model_name):
        self.polytube_models[new_model_name] = self.polytube_models[model_name]
        self.polytube_models[new_model_name].name = new_model_name
        del self.polytube_models[model_name]
        if self.active_polytube_model == model_name:
            self.active_polytube_model = new_model_name
        self.polytube_models[new_model_name].\
          set_tips_visibility(self.polytube_tips_enabled)

    def get_active_polytube_model(self):
        return self.polytube_models.get(self.active_polytube_model)

    def get_active_voxel_model(self):
        return self.voxel_models.get(self.active_voxel_model)

    # P is a numpy array of 3d points
    def add_point_cloud(self, P, pc_name, color_name='red',
                      set_active=True, excluded=set(), up=None):
        # remove if already existing
        if pc_name in self.point_clouds:
            self.point_clouds[pc_name].delete()
        self.point_clouds[pc_name] = PointCloud(P, self.frame, pc_name,
                                                color_name, excluded, up)
        if self.point_cloud_selection_enabled:
            for sphere in self.actor_to_sphere.values():
                sphere.select_point_cloud()
        if set_active:
            self.active_point_cloud = pc_name
        self.frame.ren.ResetCamera()
        self.frame.ren_win.Render()

    def get_point_cloud(self, pc_name):
        return self.point_clouds[pc_name]

    def set_active_point_cloud(self, pc_name):
        assert pc_name in self.point_clouds
        self.active_point_cloud = pc_name
        self.get_active_point_cloud().set_visible(True)

    def set_point_cloud_visibility(self, pc_name, b):
        if pc_name in self.point_clouds:
            self.point_clouds[pc_name].set_visible(b)

    def load_model_or_markers(self, fn):
        f = open(fn)
        header = f.readline()
        if header.strip() == 'node_id,parent_node_id,x,y,z,radius':
            f.close()
            K = TreeModel()
            K.load(fn)
            self.add_polytube_model(K, os.path.splitext(os.path.basename(fn))[0],
                                  show_volume=self.polytube_volume_enabled,
                                  color_tips_in_yellow=self.polytube_tips_enabled)
            return 'model'
        elif header.strip() == 'x,y,z,radius,relative_distance,'\
                               'cumulative_distance':
            for mm_rank, line in enumerate(f):
                if not line.strip(): continue
                values = [float(v) for v in line.split(',')]
                sphere = ArticulationSphere(pos=harray(values[:3]),
                                            radius=values[3], frame=self.frame,
                                            scene=self, color='yellow')
                sphere.mm_rank = mm_rank
                self.actor_to_sphere[sphere.actor] = sphere
                return 'markers'
        else: raise Exception('unknown csv header')

    def set_point_cloud_selection(self, b):
        self.point_cloud_selection_enabled = b
        for sphere in self.actor_to_sphere.values():
            if b:
                sphere.select_point_cloud()
            else:
                sphere.unselect_point_cloud()

    def set_polytube_volume(self, b):
        self.polytube_volume_enabled = b
        if self.get_active_polytube_model():
            self.get_active_polytube_model().set_volume(b)

    # G is a NetworkX graph with nodes corresponding to self.point_clouds[pc]
    def set_point_cloud_graph(self, G, pc_name=None):
        if not pc_name: pc_name = self.active_point_cloud
        lines = vtk.vtkCellArray()
        for edge in G.edges():
            lines.InsertNextCell(2)
            lines.InsertCellPoint(edge[0])
            lines.InsertCellPoint(edge[1])
        self.point_clouds[pc_name].polydata.SetLines(lines)
        self.frame.ren_win.Render()

    def unset_point_cloud_graph(self, pc_name=None):
        if not pc_name: pc_name = self.active_point_cloud
        self.point_clouds[pc_name].polydata.SetLines(None)
        self.frame.ren_win.Render()

    # color_scheme: list of (color_name, points)'s
    def set_point_cloud_color_scheme(self, color_scheme, pc_name=None):
        if not pc_name: pc_name = self.active_point_cloud
        for color_name, pts in color_scheme:
            for i in pts:
                color = name_to_rgb(color_name)
                self.point_clouds[pc_name].colors.SetTuple3(i, *color)
        self.point_clouds[pc_name].colors.Modified()
        self.frame.ren_win.Render()

    def unset_point_cloud_color_scheme(self, pc_name=None):
        if not pc_name: pc_name = self.active_point_cloud
        self.point_clouds[pc_name].reset_colors()

    def add_polytube_model(self, K, model_name, color_tips_in_yellow=False,
                         show_volume=True, additional_sphere_callbacks=None):
        # remove if already existing
        if model_name in self.polytube_models:
            self.polytube_models[model_name].delete()
        if additional_sphere_callbacks is None:
            additional_sphere_callbacks = []
        self.polytube_models[model_name] = PolytubeModel(self, K, model_name,
                                            color_tips_in_yellow, show_volume,
                                            additional_sphere_callbacks)
        self.active_polytube_model = model_name

    def set_active_polytube_model(self, model_name):
        assert model_name in self.polytube_models
        self.active_polytube_model = model_name
        self.get_active_polytube_model().set_visible(True)

    def set_polytube_model_visibility(self, model_name, is_visible):
        if model_name in self.polytube_models:
            self.polytube_models[model_name].set_visible(is_visible)

    def set_polytube_model_tips_visibility(self, are_visible):
        if self.get_active_polytube_model():
            self.get_active_polytube_model().set_tips_visibility(are_visible)
        self.polytube_tips_enabled = are_visible

    def delete_articulation_sphere(self, sphere):
        del self.actor_to_sphere[sphere.actor]
        sphere.delete()

    def add_articulation_sphere(self, pos2d):
        if not self.get_active_point_cloud(): return
        self.get_active_point_cloud().actor.SetPickable(True)
        picker = vtk.vtkPointPicker()
        if picker.Pick(pos2d[0], pos2d[1], 0, self.frame.ren):
            pos = picker.GetPickPosition()
            sphere = ArticulationSphere(pos=pos,
                            radius=ArticulationSphere.last_radius_update,
                            frame=self.frame, scene=self,
                            color=self.get_active_point_cloud().base_color)
            self.actor_to_sphere[sphere.actor] = sphere
        self.get_active_point_cloud().actor.SetPickable(False)

    def unselect_all_articulation_spheres(self):
        for sphere in self.actor_to_sphere.values():
            sphere.set_selected(False)

    def add_voxel_model(self, V, model_name, opacity=1, color='gray'):
        if model_name in self.voxel_models:
            self.voxel_models[model_name].delete()
        self.voxel_models[model_name] = VoxelModel(self, V, opacity, color)
        self.active_voxel_model = model_name

    def set_active_voxel_model(self, model_name):
        assert model_name in self.voxel_models
        self.active_voxel_model = model_name
        self.get_active_voxel_model().set_visible(True)

    # make sure that the MM are sorted according to their rank (0=low, last=high)
    def get_measurement_markers(self):
        mms = [] # (rank, sphere)'s
        for s in self.actor_to_sphere.values():
            if s.color == 'yellow': mms.append((s.mm_rank, s))
        return [s for r, s in sorted(mms)]

    def save_measurement_markers(self, fn):
        f = open(fn, 'w')
        f.write('x,y,z,radius,relative_distance,cumulative_distance\n')
        cumul_dist = 0
        rel_dist = 0
        mms = self.get_measurement_markers()
        for i, s in enumerate(mms):
            pos = s.get_position()
            if i > 0: rel_dist = dist(pos, mms[i-1].get_position())
            cumul_dist += rel_dist
            f.write('%f,%f,%f,%f,%f,%f\n' % (pos[0], pos[1], pos[2],
                                             s.get_radius(), rel_dist,
                                             cumul_dist))
        f.close()

    def clear_measurement_markers(self):
        for s in self.get_measurement_markers():
            self.delete_articulation_sphere(s)

    def save_screenshot(self, fn, ext):
        if ext.lower() == '.eps':
            exporter = vtk.vtkGL2PSExporter()
            exporter.SetFileFormatToEPS()
            #exporter.CompressOn()
            exporter.SetFilePrefix(fn)
            exporter.SetRenderWindow(self.frame.ren_win)
            exporter.Write()
        # elif ext.lower() in ['.png', '.tiff', '.jpg']:
        #     win_to_img_filter = vtk.vtkWindowToImageFilter()
        #     win_to_img_filter.SetInput(self.frame.ren_win)
        #     #win_to_img_filter.SetMagnification(3)
        #     #win_to_img_filter.SetInputBufferTypeToRGBA()
        ##         also record the alpha (transparency) channel
        #     win_to_img_filter.Update()
        #     if ext.lower() == '.png':
        #         writer = vtk.vtkPNGWriter()
        #     elif ext.lower() == '.jpg':
        #         writer = vtk.vtkJPEGWriter()
        #     elif ext.lower() == '.tiff':
        #         writer = vtk.vtkTIFFWriter()
        #     writer.SetFileName(fn + ext)
        #     writer.SetInputConnection(win_to_img_filter.GetOutputPort())
        #     writer.Write()
        # else:
        #     raise Exception('unknown file type (%s)' % ext)

class PointCloud:

    def __init__(self, P, frame, name, base_color='red',
                 excluded=set(), up=None):

        self.name = name
        pts = vtk.vtkPoints()
        cells = vtk.vtkCellArray()
        self.base_color = base_color
        self.colors = vtk.vtkUnsignedCharArray()
        self.colors.SetNumberOfComponents(3)
        self.colors.SetName('colors')
        i = 0
        for j, p in enumerate(P):
            if j not in excluded:
                pts.InsertNextPoint(p)
                cells.InsertNextCell(1)
                cells.InsertCellPoint(i)
                self.colors.InsertTuple3(i, *name_to_rgb(self.base_color))
                i += 1
        if excluded:
            self.P = P[list(set(range(len(P))) - excluded)]
        else:
            self.P = P
        self.polydata = vtk.vtkPolyData()
        self.polydata.SetPoints(pts)
        self.polydata.SetVerts(cells)
        self.polydata.GetPointData().SetScalars(self.colors)
        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInput(self.polydata)
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)
        self.actor.SetPickable(False) # not sure if this is needed
        self.actor.GetProperty().SetPointSize(2)
        self.frame = frame
        self.frame.ren.AddActor(self.actor)
        self.frame.ren_win.Render()
        # counters used for overlapping selection detection
        self.selected_pts = defaultdict(int)
        self.up = up # upward dim: 0, 1 or 2

    def delete(self):
        self.frame.ren.RemoveActor(self.actor)
        self.frame.ren_win.Render()

    def reset_colors(self):
        for i in range(len(self.P)):
            self.colors.SetTuple3(i, *name_to_rgb(self.base_color))
        self.colors.Modified()
        self.frame.ren_win.Render()

    def set_visible(self, b):
        self.actor.SetVisibility(b)
        self.frame.ren_win.Render()

class ArticulationSphere:

    last_radius_update = INIT_SPHERE_RADIUS

    def __init__(self, pos, radius=None, frame=None, scene=None, color='gray'):
        if radius is None:
            radius = ArticulationSphere.last_radius_update
        self.init_radius = radius
        self.src = vtk.vtkSphereSource()
        self.src.SetThetaResolution(16)
        self.src.SetPhiResolution(16)
        self.src.SetCenter(pos)
        self.src.SetRadius(radius)
        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInput(self.src.GetOutput())
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)
        self.color = color # base color name
        self.set_color()
        self.actor.GetProperty().SetOpacity(0.25)
        self.frame = frame
        self.frame.ren.AddActor(self.actor)
        self.scene = scene
        self.selected_pts = []
        self.is_selected = False
        if self.scene.point_cloud_selection_enabled:
            self.select_point_cloud()
        self.callbacks = defaultdict(lambda: [lambda a: None])
        # action_name -> list of callbacks to be called
        # after action is performed (i.e. 'moved', 'delete', etc)
        self.polytube_node = None # None -> sphere is "roaming"
                                  #         (i.e. not attached to any model)
        self.frame.ren_win.Render()

    def unselect_point_cloud(self):
        if not self.scene.get_active_point_cloud(): return
        bc = self.scene.get_active_point_cloud().base_color
        for i in self.selected_pts:
            self.scene.get_active_point_cloud().selected_pts[i] -= 1
            if self.scene.get_active_point_cloud().selected_pts[i] == 0:
                self.scene.get_active_point_cloud().\
                  colors.SetTuple3(i, *name_to_rgb(bc))
        self.scene.get_active_point_cloud().colors.Modified()
        self.frame.ren_win.Render()

    # select the points inside the current intersection
    # of the sphere with the point cloud
    def select_point_cloud(self):
        if not self.scene.get_active_point_cloud(): return
        self.unselect_point_cloud()
        transform = vtk.vtkTransform()
        transform.SetMatrix(self.actor.GetMatrix())
        transform_filter = vtk.vtkTransformPolyDataFilter()
        transform_filter.SetInputConnection(self.src.GetOutputPort())
        transform_filter.SetTransform(transform)
        enclosed_pts = vtk.vtkSelectEnclosedPoints()
        enclosed_pts.SetInput(self.scene.get_active_point_cloud().polydata)
        enclosed_pts.SetSurface(transform_filter.GetOutput())
        enclosed_pts.Update()
        inside_arr = enclosed_pts.GetOutput().GetPointData().\
          GetArray('SelectedPoints')
        self.selected_pts = []
        for i in range(inside_arr.GetNumberOfTuples()):
            if inside_arr.GetComponent(i, 0):
                self.scene.get_active_point_cloud().colors.\
                  SetTuple3(i, *name_to_rgb('blue'))
                self.selected_pts.append(i)
                self.scene.get_active_point_cloud().selected_pts[i] += 1
        self.scene.get_active_point_cloud().colors.Modified()
        self.frame.ren_win.Render()

    # blue
    def toggle_selected(self):
        self.is_selected = not self.is_selected
        self.set_selected(self.is_selected)

    # blue
    def set_selected(self, b):
        if b: self.set_color('blue')
        else: self.set_color()
        self.is_selected = b
        self.frame.ren_win.Render()

    def set_color(self, color_name=None):
        self.actor.GetProperty().SetColor(
            name_to_rgb_float(color_name if color_name else self.color))

    def get_position(self):
        return harray(self.actor.GetCenter())

    def set_position(self, p):
        self.actor.SetPosition(p - harray(self.src.GetCenter()))

    def get_radius(self):
        return self.init_radius * self.actor.GetScale()[0]

    def set_radius(self, r):
        org = self.get_position() - harray(self.actor.GetPosition())
        self.actor.SetOrigin(org)
        self.actor.SetScale(r / self.init_radius)

    def update(self):
        ArticulationSphere.last_radius_update = self.get_radius()
        # selection
        if self.scene.point_cloud_selection_enabled:
            self.select_point_cloud()

    def delete(self):
        if not hasattr(self, 'src'): return
        del self.src, self.mapper
        self.frame.ren.RemoveActor(self.actor)
        del self.actor
        self .unselect_point_cloud()
        self.frame.ren_win.Render()

    def add_callback(self, name, f):
        self.callbacks[name].append(f)

    def run_callbacks(self, name):
        for f in self.callbacks[name]: f(self)

    def remove_callback(self, name):
        del self.callbacks[name]

    def set_visible(self, b):
        self.actor.SetVisibility(b)
        if not b:
            self.unselect_point_cloud()
        elif self.scene.point_cloud_selection_enabled:
            self.select_point_cloud()

    def delete_selected_points(self):
        pc = self.scene.get_active_point_cloud()
        n_selected = len(self.selected_pts)
        self.scene.add_point_cloud(pc.P, pc.name, pc.base_color,
                                 True, set(self.selected_pts))
        pc.delete()
        return n_selected

    def stitch_neighborhood_graph(self, N):
        for i in self.selected_pts:
            for j in self.selected_pts:
                if i == j: continue
                N.add_edge(i, j,
                           weight=dist(self.scene.get_active_point_cloud().P[i],
                                       self.scene.get_active_point_cloud().P[j]))

    # # not used (buggy)
    # def contract(self):
    #     if not self.scene.point_cloud_selection_enabled:
    #         self.select_point_cloud(show=False)
    #     if len(self.selected_pts) < 10: return
    #     c = mean(self.scene.getActivePointCloud().\
    #                                 P[[self.selected_pts]], axis=0)
    #     #avg_d = 0.0
    #     max_d = float('-inf')
    #     for i in self.selected_pts:
    #         d = dist(c, self.scene.getActivePointCloud().P[i])
    #         #avg_d += d
    #         max_d = max(d, max_d)
    #     #avg_d /= len(self.selected_pts)
    #     radius = max_d #+ (.25 * max_d)
    #     q = c - self.get_position()
    #     self.actor.AddPosition(*q)
    #     scale = radius / self.init_radius
    #     org = array(self.get_position()) - array(self.actor.GetPosition())
    #     self.actor.SetOrigin(org)
    #     self.actor.SetScale(scale)
    #     self.update()
    #     self.frame.ren_win.Render()

class PolytubeModel:

    # additional_sphere_callbacks: list of (callback_name, callback)'s
    def __init__(self, scene, K, name, color_tips_in_yellow=False,
                 show_volume=True, additional_sphere_callbacks=None, color='gray'):
        self.scene = scene
        self.frame = scene.frame
        self.K = K # TreeModel instance
        self.name = name
        self.base_color = color
        self.color_tips_in_yellow = color_tips_in_yellow
        self.show_volume = show_volume
        self.node_to_sphere = {}
        if additional_sphere_callbacks is None:
            self.additional_sphere_callbacks = []
        else:
            self.additional_sphere_callbacks = additional_sphere_callbacks
        self.actor = None
        self.generate()

    def generate(self):
        if self.actor is not None:
            self.frame.ren.RemoveActor(self.actor)
        self.pts = vtk.vtkPoints()
        self.radii = vtk.vtkFloatArray()
        self.radii.SetName('radii')
        self.colors = vtk.vtkUnsignedCharArray()
        self.colors.SetNumberOfComponents(3)
        self.colors.SetName('colors')
        # nodes
        for k, node in self.K.items():
            self.pts.InsertPoint(k, *node.pos)
            self.radii.InsertTuple1(k, node.radius)
            if self.color_tips_in_yellow and not node.children:
                self.colors.InsertTuple3(k, *name_to_rgb('yellow'))
            else:
                self.colors.InsertTuple3(k, *name_to_rgb(self.base_color))
        # edges
        lines = vtk.vtkCellArray()
        for k, node in self.K.items():
            if node.parent is None: continue
            lines.InsertNextCell(2)
            lines.InsertCellPoint(k)
            lines.InsertCellPoint(node.parent)
        self.polydata = vtk.vtkPolyData()
        self.polydata.SetPoints(self.pts)
        self.polydata.SetLines(lines)
        self.polydata.GetPointData().AddArray(self.radii)
        self.polydata.GetPointData().AddArray(self.colors)
        self.polydata.GetPointData().SetActiveScalars('radii')
        self.tubes = vtk.vtkTubeFilter()
        self.tubes.SetNumberOfSides(10)
        self.tubes.SetInput(self.polydata)
        self.tubes.SetVaryRadiusToVaryRadiusByAbsoluteScalar()
        self.tubes.CappingOn()
        self.mapper = vtk.vtkPolyDataMapper()
        if self.show_volume:
            self.mapper.SetInput(self.tubes.GetOutput())
        else:
            self.mapper.SetInput(self.polydata)
        self.mapper.ScalarVisibilityOn()
        self.mapper.SetScalarModeToUsePointFieldData()
        self.mapper.SelectColorArray('colors')
        self.actor = vtk.vtkActor()
        self.actor.GetProperty().SetColor(name_to_rgb_float(self.base_color))
        self.actor.SetMapper(self.mapper)
        self.frame.ren.AddActor(self.actor)
        self.frame.ren_win.Render()

    def set_volume(self, b):
        self.show_volume = b
        if b:
            self.mapper.SetInput(self.tubes.GetOutput())
        else:
            self.mapper.SetInput(self.polydata)
        self.frame.ren_win.Render()

    def set_visible(self, b):
        self.actor.SetVisibility(b)
        for s in self.node_to_sphere.values():
            s.set_visible(b)
        self.frame.ren_win.Render()

    def delete(self):
        self.frame.ren.RemoveActor(self.actor)
        for s in self.node_to_sphere.values():
            self.scene.delete_articulation_sphere(s)
        self.frame.ren_win.Render()

    def update(self, sphere):
        self.pts.SetPoint(sphere.polytube_node, sphere.get_position())
        self.pts.Modified()
        self.radii.SetTuple1(sphere.polytube_node,
                             sphere.get_radius() / ART_SPHERE_SIZE_RATIO)
        self.radii.Modified()
        self.K[sphere.polytube_node].pos = sphere.get_position()
        self.K[sphere.polytube_node].radius = (sphere.get_radius() /
                                               ART_SPHERE_SIZE_RATIO)
        self.frame.ren_win.Render()

    def _cut(self, visited):
        for k in visited:
            if k in self.node_to_sphere:
                self.scene.delete_articulation_sphere(self.node_to_sphere[k])
                del self.node_to_sphere[k]
        self.generate()

    def cut_above(self, sphere):
        self._cut(self.K.cut(sphere.polytube_node, point='above'))

    def cut_branch(self, sphere):
        self._cut(self.K.cut(sphere.polytube_node,
                             point='down_nearest_branching'))

    def delete_articulation_sphere(self, sphere):
        del self.node_to_sphere[sphere.polytube_node]

    def add_articulation_sphere_to_closest_point(self, pos2d):
        picker = vtk.vtkPointPicker()
        if not picker.Pick(pos2d[0], pos2d[1], 0, self.frame.ren): return
        p = picker.GetPickPosition()
        k, node = min([(linalg.norm(node.pos - p),
                        (k, node)) for k, node in self.K.items()])[1]
        if k in self.node_to_sphere: return # already one
        sphere = ArticulationSphere(pos=node.pos, frame=self.frame,
                                    scene=self.scene,
                                    radius=node.radius * ART_SPHERE_SIZE_RATIO,
                                    color=self.base_color)
        sphere.add_callback('moved', self.update)
        sphere.add_callback('cut_above', self.cut_above)
        sphere.add_callback('cut_branch', self.cut_branch)
        sphere.add_callback('delete', self.delete_articulation_sphere)
        for name, f in self.additional_sphere_callbacks:
            sphere.add_callback(name, f)
        sphere.polytube_node = k
        self.node_to_sphere[k] = sphere
        self.scene.actor_to_sphere[sphere.actor] = sphere

    def connect_articulation_sphere_to_closest_point(self, sphere, pos2d):
        if sphere.polytube_node is not None: return # already connected
        picker = vtk.vtkPointPicker()
        if not picker.Pick(pos2d[0], pos2d[1], 0, self.frame.ren): return
        p = picker.GetPickPosition()
        k, node = min([(linalg.norm(node.pos - p),
                        (k, node)) for k, node in self.K.items()])[1]
        new_node = self.K.add_node(pos=sphere.get_position(),
                                  radius=(sphere.get_radius() /
                                          ART_SPHERE_SIZE_RATIO),
                                  parent=k)
        self.K[k].children.add(new_node.id)
        self.node_to_sphere[new_node.id] = sphere
        sphere.polytube_node = new_node.id
        sphere.add_callback('moved', self.update)
        sphere.add_callback('cut_above', self.cut_above)
        sphere.add_callback('cut_branch', self.cut_branch)
        sphere.add_callback('delete', self.delete_articulation_sphere)
        for name, f in self.additional_sphere_callbacks:
            sphere.add_callback(name, f)
        self.generate()

    def set_tips_visibility(self, are_visible):
        self.color_tips_in_yellow = are_visible
        for k, node in self.K.items():
            if self.color_tips_in_yellow and not node.children:
                self.colors.SetTuple3(k, *name_to_rgb('yellow'))
            else:
                self.colors.SetTuple3(k, *name_to_rgb(self.base_color))
        self.colors.Modified()
        self.frame.ren_win.Render()

    def add_user_measurement_markers(self):

        def update_user_measurement_marker(sphere):
            pos, rad, k = self.K.calibrate_user_measurement_marker(
                                                        sphere.get_position())
            sphere.set_position(pos)
            sphere.set_radius(rad)
            sphere.mm_node = k

        added = [False, False]
        self.mm_user_spheres = []
        self.mm_spheres = []
        for k, node in self.K.items():
            if self.K[k].is_root_node(): continue
            #if self.K[k].is_root_node() and not added[0]:
            if self.K[self.K[k].parent].is_root_node() and not added[0]:
                sphere = ArticulationSphere(pos=self.K[self.K[k].parent].pos,
                                            frame=self.frame, scene=self.scene,
                                            radius=node.radius, color='green')
                sphere.add_callback('moved', update_user_measurement_marker)
                sphere.mm_node = k
                self.scene.actor_to_sphere[sphere.actor] = sphere
                self.mm_user_spheres.append(sphere)
                added[0] = True
            elif self.K[k].is_tip_node() and not added[1]:
                sphere = ArticulationSphere(pos=node.pos, frame=self.frame,
                                            scene=self.scene,
                                            radius=node.radius, color='green')
                sphere.add_callback('moved', update_user_measurement_marker)
                sphere.mm_node = k
                self.scene.actor_to_sphere[sphere.actor] = sphere
                self.mm_user_spheres.append(sphere)
                added[1] = True
            if all(added): break

    def find_interpolated_measurement_markers(self, n_markers):
        for s in self.mm_spheres: self.scene.delete_articulation_sphere(s)
        self.mm_spheres = []
        markers = self.K.find_interpolated_measurement_markers(
                                                self.mm_user_spheres, n_markers)
        if not markers: return False
        for mm_rank, (pos, rad) in enumerate(markers, 1):
            sphere = ArticulationSphere(pos=pos, frame=self.frame,
                                        scene=self.scene, radius=rad,
                                        color='yellow')
            sphere.mm_rank = mm_rank
            self.scene.actor_to_sphere[sphere.actor] = sphere
            self.mm_spheres.append(sphere)
        return True

    def clear_current_measurement_markers(self):
        for s in self.mm_user_spheres + self.mm_spheres:
            self.scene.delete_articulation_sphere(s)
        del self.mm_user_spheres
        del self.mm_spheres

    def commit_current_measurement_markers(self):
        # b = 0 is lower than 1
        b = (self.K[self.mm_user_spheres[0].mm_node].level <
             self.K[self.mm_user_spheres[1].mm_node].level)
        self.mm_user_spheres[0 if b else 1].mm_rank = 0
        self.mm_user_spheres[1 if b else 0].mm_rank = len(self.mm_spheres) + 1
        assert (self.mm_user_spheres[1 if b else 0].mm_rank ==
                self.mm_spheres[-1].mm_rank + 1)
        for s in self.mm_user_spheres:
            s.remove_callback('moved')
            s.color = 'yellow'
            s.set_color()
        del self.mm_user_spheres
        del self.mm_spheres

class VoxelModel:

    # def __init__(self, scene, V, opacity=1, color='gray'):
    #     self.scene = scene
    #     self.frame = scene.frame
    #     self.V = V
    #     grid = vtk.vtkImageData()
    #     grid.SetOrigin(*V.low_range)
    #     grid.SetDimensions(*V.get_bin_dims())
    #     grid.SetSpacing(V.bin_size, V.bin_size, V.bin_size)
    #     vis_arr = vtk.vtkIntArray()
    #     vis_arr.SetNumberOfTuples(grid.GetNumberOfCells())
    #     vis_arr.SetNumberOfComponents(1)
    #     vis_arr.SetName('visibility')
    #     for q in V:
    #         vis_arr.InsertValue(grid.ComputeCellId(q), 1)
    #     grid.GetCellData().AddArray(vis_arr)
    #     thresh = vtk.vtkThreshold()
    #     thresh.SetInputConnection(grid.GetProducerPort())
    #     thresh.ThresholdByUpper(.5)
    #     thresh.SetInputArrayToProcess(0,0,0,1, 'visibility')
    #     mapper = vtk.vtkDataSetMapper()
    #     mapper.SetInputConnection(thresh.GetOutputPort())
    #     self.actor = vtk.vtkActor()
    #     self.actor.SetMapper(mapper)
    #     self.actor.GetProperty().SetColor(*name_to_rgb_float(color))
    #     self.actor.GetProperty().SetOpacity(opacity)
    #     self.frame.ren.AddActor(self.actor)

    # def __init__(self, scene, V, opacity=1, color='gray'):
    #     self.scene = scene
    #     self.frame = scene.frame
    #     self.V = V
    #     grid = vtk.vtkImageData()
    #     grid.SetOrigin(*V.low_range)
    #     grid.SetDimensions(*V.get_bin_dims())
    #     grid.SetSpacing(V.bin_size, V.bin_size, V.bin_size)
    #     grid.SetScalarTypeToInt()
    #     grid.AllocateScalars()
    #     for q in V:
    #         grid.SetScalarComponentFromFloat(q[0], q[1], q[2], 0, 1)
    #     surface = vtk.vtkDiscreteMarchingCubes()
    #     surface.SetInput(grid)
    #     surface.ComputeScalarsOff()
    #     surface.SetValue(0, 1)
    #     mapper = vtk.vtkPolyDataMapper()
    #     mapper.SetInputConnection(surface.GetOutputPort())
    #     self.actor = vtk.vtkActor()
    #     self.actor.SetMapper(mapper)
    #     self.actor.GetProperty().SetColor(*name_to_rgb_float(color))
    #     self.actor.GetProperty().SetOpacity(opacity)
    #     self.frame.ren.AddActor(self.actor)

    def __init___(self, scene, V, opacity=1, color='gray'):
        self.scene = scene
        self.frame = scene.frame
        self.V = V
        n_voxels = len(V)
        size = V.bin_size
        pts = vtk.vtkPoints()
        pts.SetNumberOfPoints(8 * n_voxels)
        grid = vtk.vtkUnstructuredGrid()
        grid.Allocate(n_voxels, 1)
        vx = vtk.vtkVoxel()
        for i, q in enumerate(V):
            pos = q * size + V.low_range
            pts.InsertPoint(i * 8 + 0, *pos)
            pts.InsertPoint(i * 8 + 1, *(pos + (size,0,0)))
            pts.InsertPoint(i * 8 + 2, *(pos + (0,size,0)))
            pts.InsertPoint(i * 8 + 3, *(pos + (size,size,0)))
            pts.InsertPoint(i * 8 + 4, *(pos + (0,0,size)))
            pts.InsertPoint(i * 8 + 5, *(pos + (size,0,size)))
            pts.InsertPoint(i * 8 + 6, *(pos + (0,size,size)))
            pts.InsertPoint(i * 8 + 7, *(pos + (size,size,size)))
            for j in range(8):
                vx.GetPointIds().SetId(j, i * 8 + j)
            grid.InsertNextCell(vx.GetCellType(), vx.GetPointIds())
        grid.SetPoints(pts)
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInput(grid)
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        #self.actor.GetProperty().SetDiffuseColor(*name_to_rgb_float(color))
        self.actor.GetProperty().SetColor(*name_to_rgb_float(color))
        self.actor.GetProperty().SetOpacity(opacity)
        self.frame.ren.AddActor(self.actor)

    def __init__(self, scene, V, opacity=1, color='gray'):
        self.scene = scene
        self.frame = scene.frame
        delaunay = vtk.vtkDelaunay3D()
        delaunay.SetInput(self.scene.get_active_point_cloud().polydata)
        delaunay.SetAlpha(V.bin_size)
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInput(delaunay.GetOutput())
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        self.actor.GetProperty().SetColor(*name_to_rgb_float(color))
        self.actor.GetProperty().SetOpacity(opacity)
        self.frame.ren.AddActor(self.actor)

    def delete(self):
        self.frame.ren.RemoveActor(self.actor)
        self.frame.ren_win.Render()
