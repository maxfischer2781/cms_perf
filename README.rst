=================================
``cms_perf`` - XRootD load sensor
=================================

.. image:: https://readthedocs.org/projects/cms-perf/badge/?version=latest
    :target: http://cms-perf.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/cms_perf.svg
    :alt: Available on PyPI
    :target: https://pypi.python.org/pypi/cms_perf/

.. image:: https://img.shields.io/github/license/maxfischer2781/cms_perf.svg
    :alt: License
    :target: https://github.com/maxfischer2781/cms_perf/blob/master/LICENSE

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.4011821.svg
   :target: https://doi.org/10.5281/zenodo.4011821

Sensor for use in the XRootD ``cms.perf`` directive.
Measures system load, as well as cpu, memory, and network utilization,
to enable load-balancing in a cluster of multiple XRootD servers.

With its support for individual re-configuration of each sensor reading,
``cms_perf`` allows to fine-tune or even re-define load reporting to your needs.
No need to hack any scripts, just install, configure, run.

Installation and Usage
======================

The sensor can be installed using ``pip``,
then configured using the ``cms.perf`` directive.
See the `documentation`_ for details and examples.

Issues and Contributions
========================

Maintenance and development of ``cms.perf`` is hosted at `GitHub`_.
For technical issues or suggestions, please open an issue ticket.
For direct code submissions, please open a pull request.

.. _documentation: https://cms-perf.readthedocs.io/
.. _GitHub: https://github.com/maxfischer2781/cms_perf
