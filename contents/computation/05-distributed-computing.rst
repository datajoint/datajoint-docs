.. progress: 12.0 20% Dimitri

.. _distributed:

Distributed Computing
=====================

Job reservations
----------------

Running ``populate`` on the same table on multiple computers will causes them to attempt to compute the same data all at once.
This will not corrupt the data since DataJoint will reject any duplication.
One solution could be to cause the different computing nodes to populate the tables in random order.
This would reduce some collisions but not completely prevent them.

To allow efficient distributed computing, DataJoint provides a built-in job reservation process.
When ``dj.Computed`` tables are auto-populated using job reservation, a record of each ongoing computation is kept in a schema-wide ``jobs`` table, which is used internally by DataJoint to coordinate the auto-population effort among multiple computing processes.


.. include:: 06-distributed-computing_lang1.rst

With job management enabled, the ``make`` method of each table class will also consult the ``jobs`` table for reserved jobs as part of determining the next record to compute and will create an entry in the ``jobs`` table as part of the attempt to compute the resulting record for that key.
If the operation is a success, the record is removed.
In the event of failure, the job reservation entry is updated to indicate the details of failure.
Using this simple mechanism, multiple processes can participate in the auto-population effort without duplicating computational effort, and any errors encountered during the course of the computation can be individually inspected to determine the cause of the issue.

As part of DataJoint, the jobs table can be queried using native DataJoint syntax. For example, to list the jobs currently being run:

.. include:: 06-distributed-computing_lang2.rst


The above output shows that a record for the ``JobResults`` table is currently reserved for computation, along with various related details of the reservation, such as the MySQL connection ID, client user and host, process ID on the remote system, timestamp, and the key for the record that the job is using for its computation.
Since DataJoint table keys can be of varying types, the key is stored in a binary format to allow the table to store arbitrary types of record key data.
The subsequent sections will discuss querying the jobs table for key data.

As mentioned above, jobs encountering errors during computation will leave their record reservations in place, and update the reservation record with details of the error.

.. include:: 06-distributed-computing_lang3.rst


By leaving the job reservation record in place, the error can be inspected, and if necessary the corresponding ``dj.Computed`` update logic can be corrected.
From there the jobs entry can be cleared, and the computation can then be resumed.
In the meantime, the presence of the job reservation will prevent this particular record from being processed during subsequent auto-population calls.
Inspecting the job record for failure details can proceed much like any other DataJoint query.

.. include:: 06-distributed-computing_lang4.rst

After any system or code errors have been resolved, the table can simply be cleaned of errors and the computation rerun.

.. include:: 06-distributed-computing_lang5.rst

In some cases, it may be preferable to inspect the jobs table records using populate keys.
Since job keys are hashed and stored as a blob in the jobs table to support the varying types of keys, we need to query using the key hash instead of simply using the raw key data.

.. include: 06-distributed-computing_jobs_by_key.rst

Managing connections
--------------------

The DataJoint method ``dj.kill`` allows for viewing and termination of database connections.
Restrictive conditions can be used to identify specific connections.
Restrictions are specified as strings and can involve any of the attributes of ``information_schema.processlist``: ``ID``, ``USER``, ``HOST``, ``DB``, ``COMMAND``, ``TIME``, ``STATE``, and ``INFO``.

Examples:

  ``dj.kill('HOST LIKE "%compute%"')`` lists only connections from hosts containing "compute".
  ``dj.kill('TIME > 600')`` lists only connections older than 10 minutes.

A list of connections meeting the restriction conditions (if present) are presented to the user, along with the option to kill processes. By default, output is ordered by ascending connection ID. To change the output order of dj.kill(), an additional order_by argument can be provided.

.. include:: 06-distributed-computing_kill_order_by.rst

.. |python| image:: ../_static/img/python-tiny.png
.. |matlab| image:: ../_static/img/matlab-tiny.png
