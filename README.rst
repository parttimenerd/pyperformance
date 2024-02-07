##########################
The Python Benchmark Suite
##########################

.. image:: https://img.shields.io/pypi/v/pyperformance.svg
   :alt: Latest pyperformance release on the Python Cheeseshop (PyPI)
   :target: https://pypi.python.org/pypi/pyperformance

.. image:: https://github.com/python/pyperformance/actions/workflows/main.yml/badge.svg
   :alt: Build status of pyperformance on GitHub Actions
   :target: https://github.com/python/pyperformance/actions

The ``pyperformance`` project is intended to be an authoritative source of
benchmarks for all Python implementations. The focus is on real-world
benchmarks, rather than synthetic benchmarks, using whole applications when
possible.

* `pyperformance documentation <http://pyperformance.readthedocs.io/>`_
* `pyperformance GitHub project <https://github.com/python/pyperformance>`_
  (source code, issues)
* `Download pyperformance on PyPI <https://pypi.python.org/pypi/pyperformance>`_

pyperformance is not tuned for PyPy yet: use the `PyPy benchmarks project
<https://foss.heptapod.net/pypy/benchmarks>`_ instead to measure PyPy
performances.

pyperformance is distributed under the MIT license.


Modifications in this fork
--------------------------
This fork is modified to compare the performance of debugging via
``sys.settrace`` and ``sys.monitoring``. The debugger implementation is
minimal without any breakpoints, so it checks the basic performance
running a application under a debugger.

The used debugger mode is configured via the ``DEBUGGER_MODE`` environment
variable.

For ``sys.settrace`` (``DEBUGGER_MODE=t``), it adds the following code
to the beginning of the benchmark runner::

    import sys
    def inner_handler(*args):
        pass


    def handler(*args):
        return inner_handler

    sys.settrace(handler)


For ``sys.monitoring`` (``DEBUGGER_MODE=m`` or ``DEBUGGER_MODE=m2``), it adds
to the beginning of the benchmark runner::

    import sys
    mon = sys.monitoring
    E = mon.events
    TOOL_ID = mon.DEBUGGER_ID

    def line_handler(*args):
        pass

    def start_handler(*args):
        pass


    # register the tool
    mon.use_tool_id(TOOL_ID, "dbg")
    # register callbacks for the events we are interested in
    mon.register_callback(TOOL_ID, E.LINE, line_handler)
    mon.register_callback(TOOL_ID, E.PY_START, start_handler)
    # enable PY_START event globally
    mon.set_events(TOOL_ID, E.PY_START)
    # or for DEBUGGER_MODE=m2
    # mon.set_events(TOOL_ID, E.PY_START | E.LINE)

This might not always work (e.g. "2to3" benchmark), so compare
the results with the baseline (``DEBUGGER_MODE=``) to check if
the debugger is enabled.

Run all benchmarks via::

    python3 dev.py run -o none.json
    DEBUGGER_MODE="t" python3 dev.py run -o settrace.json
    DEBUGGER_MODE="m" python3 dev.py run -o monitoring.json
    DEBUGGER_MODE="m2" python3 dev.py run -o monitoring2.json^

Compare the results via::

    python3 analyze.py baseline-file.json result-file.json ...