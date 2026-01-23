"""
acquisition.py - Data acquisition tables

This module defines the core acquisition schema with Subject and Session tables.
Tables are declared but schema must be activated before use.
"""
import datajoint as dj

# Create schema without activating - caller must activate before use
schema = dj.Schema()


@schema
class Lab(dj.Manual):
    definition = """
    lab : varchar(32)
    ---
    institution : varchar(100)
    """


@schema
class Subject(dj.Manual):
    definition = """
    subject_id : varchar(16)
    ---
    -> Lab
    species : varchar(50)
    sex : enum('M', 'F', 'U')
    """


@schema
class Session(dj.Manual):
    definition = """
    -> Subject
    session_date : date
    ---
    session_notes : varchar(1000)
    """
