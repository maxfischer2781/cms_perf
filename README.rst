=================================
``cms_perf`` - XRootD load sensor
=================================

Sensor for use in the XRootD ``cms.perf`` directive.
Measures system load, as well as cpu, memory, and network utilization,
to enable load-balancing in a cluster of multiple XRootD servers.

Installation and Usage
======================

Use ``pip`` to install the sensor,
then configure it using the ``cms.perf`` directive.

Installing the sensor
---------------------

The sensor can be installed using the Python package manager:

.. code::

    python3 -m pip install cms_perf

.. note::

    The ``psutil`` dependency requires a C compiler and Python headers.
    On a RHEL system, use ``yum install gcc python3-devel`` to install both.
    See the `psutil documentation`_ for details and other systems.

Installing the sensor creates a ``cms_perf`` executable.

When installed for a non-standard Python, such as a venv,
the module can be run directly:

.. code::

    python3 -m cms-perf

Configuring xrootd
------------------

Add the script or module as the ``pgm`` executable of
the ``cms.perf`` directive.
Set the same interval for the directive's ``int`` and
the sensor's ``--interval``.

.. code::

    cms.perf int 5m pgm cms_perf --interval 5m

See the `cms.perf documentation`_ for details.

.. _psutil documentation: https://psutil.readthedocs.io/
.. _cms.perf documentation: https://xrootd.slac.stanford.edu/doc/dev410/cms_config.htm#_Toc8247264