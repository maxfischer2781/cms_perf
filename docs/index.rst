.. cms_perf documentation master file, created by
   sphinx-quickstart on Wed Aug 12 12:08:02 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=================================
``cms_perf`` - XRootD load sensor
=================================

.. image:: https://readthedocs.org/projects/cms_perf/badge/?version=latest
    :target: http://cms_perf.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/cms_perf.svg
    :alt: Available on PyPI
    :target: https://pypi.python.org/pypi/cms_perf/

.. image:: https://img.shields.io/github/license/maxfischer2781/cms_perf.svg
    :alt: License
    :target: https://github.com/maxfischer2781/cms_perf/blob/master/LICENSE

.. toctree::
   :maxdepth: 2
   :hidden:

   source/setup
   source/cli_lang
   source/sched

Sensor for use in the XRootD ``cms.perf`` directive.
Measures system load, as well as cpu, memory, and network utilization,
to enable load-balancing in a cluster of multiple XRootD servers.

Quick Guide
===========

The library and executable can be installed using the ``pip`` package manager:

.. code:: bash

   python3 -m pip install cms_perf

Afterwards, add the executable to the ``cms.perf`` directive in the XRootD config:

.. code::

   cms.perf int 2m pgm /usr/local/bin/cms_perf --interval 2m

See the :doc:`source/setup` and :doc:`source/cli_lang` guides for details.

Issues and Contributions
========================

Maintenance and development of ``cms.perf`` is centralised at its `GitHub Repository`_.
Feel free to open a ticket or pull request.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _GitHub Repository: https://github.com/maxfischer2781/cms_perf