.. progress: 8.0 10% Dimitri

.. _insert:

Insert
======

The ``insert`` method of DataJoint table objects inserts entities into the table.

.. include:: 1-Insert_lang1.rst

Batched inserts
---------------
Inserting a set of entities in a single ``insert`` differs from inserting the same set of entities one-by-one in a ``for`` loop in two ways:

1. Network overhead is reduced.
   Network overhead can be tens of milliseconds per query.
   Inserting 1000 entities in a single ``insert`` call may save a few seconds over inserting them individually.
2. The insert is performed as an all-or-nothing transaction.
   If even one insert fails because it violates any constraint, then none of the entities in the set are inserted.

However, inserting too many entities in a single query may run against buffer size or packet size limits of the database server.
Due to these limitations, performing inserts of very large numbers of entities should be broken up into moderately sized batches, such as a few hundred at a time.

Server-side inserts
-------------------

Data inserted into a table often come from other tables already present on the database server.
In such cases, data can be :ref:`fetched <fetch>` from the first table and then inserted into another table, but this results in transfers back and forth between the database and the local system.
Instead, data can be inserted from one table into another without transfers between the database and the local system using :ref:`queries <query-objects>`.

In the example below, a new schema has been created in preparation for phase two of a project.
Experimental protocols from the first phase of the project will be reused in the second phase.
Since the entities are already present on the database in the ``Protocol`` table of the ``phase_one`` schema, we can perform a server-side insert into ``phase_two.Protocol`` without fetching a local copy.

.. include:: 1-Insert_lang2.rst
