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
the module can be run directly by the respective python executable:

.. code::

    python3 -m cms-perf

Configuring xrootd
------------------

Add the script or module as the ``pgm`` executable of
the ``cms.perf`` directive.
Set the same interval for the directive's ``int`` and
the sensor's ``--interval``.

.. code::

    # installed for system python
    cms.perf int 2m pgm /usr/local/bin/cms_perf --interval 2m
    # installed for virtual environment
    cms.perf int 2m pgm /path/to/venv/bin/python -m cms_perf --interval 2m

See the `cms.perf documentation`_ for details of the directive.
Consult the sensor's help via ``cms_perf --help`` for details of the sensor.

Testing `cms.sched` policies
----------------------------

To gauge how a server is rated by a manager ``cms``,
``cms_perf`` allows to evaluate the total weight of the collected sensor data.
Use the ``--sched`` option and pass a ``cms.sched`` directive that you want to test;
in addition to the sensor data on stdout, the total weight is written to stderr.

.. code::

    $ python3 -m cms_perf --interval=1 --sched 'cms.sched runq 20 cpu 20 mem 60 maxload 45'
    13 1 70 0 0 44
    13 3 70 0 0 45!
    13 1 70 0 0 44
    13 1 70 0 0 44
    13 2 70 0 0 45

If ``maxload`` is given, a ``!`` indicates whether the load exceeds it.
All unused options, including the ``cms.sched`` word, are ignored and may be omitted.

.. _psutil documentation: https://psutil.readthedocs.io/
.. _cms.perf documentation: https://xrootd.slac.stanford.edu/doc/dev410/cms_config.htm#_Toc8247264