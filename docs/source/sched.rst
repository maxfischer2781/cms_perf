==================
Sched Load Testing
==================

The data provided by ``cms_perf`` on an XRootD server is eventually
weighted by an XRootD manager to select servers with the least load.
As such, a proper weighting via the ``cms.sched`` directive can be
as important as proper sampling via the ``cms.perf`` directive.
To test both directives, ``cms_perf`` can emulate the weighting of
``cms.sched`` for rapid testing on XRootD servers.

Enabling Sched Emulation
========================

The ``cms_perf`` load sensor can be supplied with a ``cms.sched``
directive to compute the total weight for each measurement.
In addition to writing the sensor data to *stdout* as usual,
the total weight is written to *stderr* as a new row.

.. code:: bash

    $ cms_perf --interval=1 --sched 'cms.sched runq 20 cpu 20 mem 60'
    13 1 70 0 0 44
    13 3 70 0 0 45
    13 1 70 0 0 44
    13 1 70 0 0 44
    13 2 70 0 0 45

The sched emulator only uses the load parameters it can process and
ignores the rest, including for example a leading *cms.sched*.

Testing Server Rejection
========================

Several optional readings of ``cms_perf``, such as the total socket count,
are designed to identify unresponsive or overloaded servers.
Ideally, an XRootD manager rejects such servers at a certain threshold
using the *maxload* option of ``cms.sched``.

Similar to the total weight, the *maxload* can be tested by ``cms_perf`` as well.
When specified, an exclamation mark is appended to each total weight that
exceeds the threshold.

.. code:: bash

    $ cms_perf --interval=1 --sched 'cms.sched runq 20 cpu 20 mem 60 maxload 45'
    13 1 70 0 0 44
    13 3 70 0 0 45!
    13 1 70 0 0 44
    13 1 70 0 0 44
    13 2 70 0 0 45!

Since the sensor does not collect data for the *space* weight,
the emulator ignores this as well.
