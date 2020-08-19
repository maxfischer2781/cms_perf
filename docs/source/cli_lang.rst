===================
CLI Sensor Language
===================

The ``cms_perf`` executable supports configuring each load sensor via the CLI.
This allows to parse mathematical expressions including the actual system sensors
to calculate the final reading.

.. code:: bash

    # allow 10x load per core than usual
    cms_perf --runq=100.0*loadq/10/ncores

Load Sensors
============

The ``cms_perf`` provides five sensor readings as percentages.
By default, they express the canonical ``cms.perf`` readings:

.. include:: ../generated/cli_sensors.rst

Sensor Expressions
==================

Each sensor can be reconfigured by supplying an expression to compute it.
Expressions use a simple language, which consists of

* float operators ``*``, ``/``, ``+``, ``-`` and parentheses,
* function calls with and without arguments, and
* constants such as numbers and enums.

Functions Calls
---------------

Various functions are built-in for use in sensor expressions.
Some of these are actual system sensors, collecting data from the system,
others are helpers to transform data, such as taking the maximum of several data points.
There are two ways to use functions in expressions:
using just the bare name to invoke default arguments,
or using the name followed by parenthesised arguments.

.. tabs::

    .. group-tab:: Default Arguments

        .. code:: bash

            # allow 10x load per physical+logical core than usual
            cms_perf --runq=100.0*loadq/10/ncores

    .. group-tab:: Custom Arguments

        .. code:: bash

            # allow 10x load per physical core than usual
            cms_perf --runq=100.0*loadq/10/ncores(physical)
