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
