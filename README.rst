***************
Post Processing
***************

Parser
======
.. automodule:: optimized_parsing

Constants
---------
.. autodata:: SIDES

.. autodata:: MESSAGE_TAGS

.. autodata:: PREFIX_COLS

Test
----
	.. autoclass:: Test
		:members:

Log
---
	.. autoclass:: Log
		:members:

Other Functions
---------------
.. automodule:: optimized_parsing
	:noindex:
	:members: make_datetime, return_or, rowvals4SQLquery, rowvals4SQLmany, rowcols4SQLquery

.. autofunction:: insert_ignore_many_query
	
Results Viewer
==============
.. automodule:: results_viewer

Constants
---------
.. autodata:: MESSAGE_TAGS

.. autodata:: SIDES

.. autodata:: TEMPERATURE_OPS

.. autodata:: DB

.. autodata:: TEST_DATA_GRAPHS

Selection Functions
-------------------
.. automodule:: results_viewer
	:noindex:
	:members: test_run_select, test_select, graph_select

Data Retrieval and Graphing Functions
-------------------------------------
.. automodule:: results_viewer
	:noindex:
	:members: get_data, determine_units, map_time2temp, generate_graph, gen_IPERF_graph, gen_temp_graph, autogenerate_graphs

Graph Helper Functions
----------------------
.. automodule:: results_viewer
	:noindex:
	:members: one_and_three_fig, tricolor_fig, double_hist_fig, my_plotter, plot_hist

Test
----
	.. autoclass:: Test
		:members:

Other Functions
---------------
.. automodule:: results_viewer
	:noindex:
	:members: return_options, return_help

Temperature Data Shifter
========================
.. automodule:: temp_data_shifter

Constants
---------
.. autodata:: RESULTS_DB

.. autodata:: TEMPS_DB

Important Functions
-------------------
.. automodule:: temp_data_shifter
	:noindex:
	:members: temp_shifter, convert_row

Other Functions
---------------
.. automodule:: temp_data_shifter
	:noindex:
	:members: round_time, rowvals4SQLquery, rowvals4SQLmany, insert_ignore_many_query


