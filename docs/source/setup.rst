======================
Installation and Usage
======================

Use ``pip`` to install the sensor,
then configure it using the ``cms.perf`` directive.
To avoid conflicts with other libraries and applications,
a Python `virtual environment`_ is recommended.

Installing the Sensor
=====================

The ``cms_perf`` library and executable are available via the ``pip`` package manager.

.. content-tabs::

    .. tab-container:: system
        :title: System Installation

        .. code:: bash

            python3 -m pip install cms_perf

    .. tab-container:: venv
        :title: VEnv Installation

        .. code:: bash

            VENV_PATH="/opt/xrootd/py3venv"  # change as desired
            python3 -m venv ${VENV_PATH}
            ${VENV_PATH}/bin/pip install cms_perf

.. note::

    The ``psutil`` dependency requires a C compiler and Python headers.
    On a RHEL system, use ``yum install gcc python3-devel`` to install both.
    See the `psutil documentation`_ for details and other systems.

Installing the sensor creates a ``cms_perf`` executable.
The module can also be run directly by the respective python executable,
e.g. ``python3 -m cms_perf``.

.. content-tabs::

    .. tab-container:: system
        :title: System Installation

        .. code:: bash

            cms_perf --help

    .. tab-container:: venv
        :title: VEnv Installation

        .. code:: bash

            ${VENV_PATH}/bin/cms_perf

.. _virtual environment: https://docs.python.org/3/library/venv.html
.. _psutil documentation: https://psutil.readthedocs.io/
