========
PypeTree
========

**PypeTree** is a Python_ and VTK_-based tool with an innovative UI
for the reconstruction and modeling of botanical trees from point
cloud data (e.g. acquired from T-LiDAR devices). From a set of
scattered 3d points, it can produce a set of truncated cones fitting
them in the most likely way. At any moment during the process, the
user can intervene by manipulating the model primitives to perform
some adjustments (to create, delete, resize or move a branch, for
instance).

.. _Python: http://www.python.org
.. _VTK: http://www.vtk.org

Features
--------

* Connectivity/geodesic-based reconstruction algorithm

.. image:: https://raw.github.com/cjauvin/pypetree/gh-pages/_images/pp_features_recon.png

* Creation and sampling of artificial models based on L-system_ rules

.. _L-system: http://en.wikipedia.org/L-system

.. image:: https://raw.github.com/cjauvin/pypetree/gh-pages/_images/pp_features_lsys.png

* Point cloud manipulation tools (here is an example of *geodesic
  clipping* of a point cloud, where the branches of its underlying
  tree model are cut above a threshold distance in its geodesic space)

.. image:: https://raw.github.com/cjauvin/pypetree/gh-pages/_images/pp_features_geoclip.png

* And many more..!
