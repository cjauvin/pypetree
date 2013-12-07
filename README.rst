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

The development of PypeTree was funded by a FQRNT_ and NSERC_ grant
obtained by `Sylvain Delagrange`_. It was created by `Christian
Jauvin`_, `Sylvain Delagrange`_ and `Pascal Rochon`_.

.. _Python: http://www.python.org
.. _VTK: http://www.vtk.org
.. _FQRNT: http://www.fqrnt.gouv.qc.ca
.. _NSERC: http://www.nserc-crsng.gc.ca/
.. _Christian Jauvin: http://christianjauv.in
.. _Sylvain Delagrange: http://services.uqo.ca/DosEtuCorpsProf/PageProfesseur.aspx?id=sylvain.delagrange
.. _Pascal Rochon: http://www.cef-cfr.ca/index.php?n=Membres.PascalRochon

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

* And much more!

Documentation
-------------

Please consult the documentation_ for an overview of how it works and how to install it.

.. _documentation: http://cjauvin.github.io/pypetree/
