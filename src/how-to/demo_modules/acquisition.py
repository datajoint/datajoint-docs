"""
acquisition.py - Data acquisition tables

This module defines the core acquisition schema with Subject and Session tables.
"""
import datajoint as dj

schema = dj.Schema('demo_acquisition')


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
