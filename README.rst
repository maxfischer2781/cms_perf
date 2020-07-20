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

.. code:: bash

    python3 -m pip install cms_perf

.. note::

    The ``psutil`` dependency requires a C compiler and Python headers.
    On a RHEL system, use ``yum install gcc python3-devel`` to install both.
    See the `psutil documentation`_ for details and other systems.

Installing the sensor creates a ``cms_perf`` executable.

When installed for a non-standard Python, such as a venv,
the module can be run directly by the respective python executable:

.. code:: bash

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

Using ``pag`` plugins
=====================

The ``pag`` (paging load) sensor is by default always 0.
``cms_perf`` avoids calculating this metric entirely,
similar to other tools such as XRootD's own ``XrdOlbMonPerf``:

.. code:: perl

   # what's the paging I/O activity ?
   # useless as this metric is highly correlated with some of the others above.
   # being kept for backward compatibility with the load balancer.
   $pgio = 0;

``cms_perf`` allows to use the ``pag`` slot for one of several plugins.
A plugin is selected by passing ``pag=<plugin name>`` to ``cms_perf``.

.. code:: bash

    $ # show help and plugins
    $ cms_perf --help
    ...
    $ # show plugin specific help
    $ python -m cms_perf pag=xrootd.num_fds -h
    ...
    $ # use sensor with plugin
    $ cms_perf --interval 10 pag=xrootd.num_fds --max-core-xfds 10
    32 10 73 32 0
    33 4 72 34 0
    ...

Testing `cms.sched` policies
============================

To gauge how a server is rated by a manager ``cms``,
``cms_perf`` allows to evaluate the total weight of the collected sensor data.
Use the ``--sched`` option and pass a ``cms.sched`` directive that you want to test;
in addition to the sensor data on stdout, the total weight is written to stderr.

.. code:: bash

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