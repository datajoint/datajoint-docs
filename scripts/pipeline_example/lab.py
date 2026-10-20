"""Who runs the experiments, and what they are run on."""

import datajoint as dj

schema = dj.Schema("lab")


@schema
class Lab(dj.Manual):
    definition = """
    lab_name : varchar(32)
    ---
    institution : varchar(64)
    """


@schema
class User(dj.Manual):
    definition = """
    -> Lab
    user_name : varchar(32)
    ---
    email : varchar(64)
    """


@schema
class Subject(dj.Manual):
    definition = """
    subject_id : int32
    ---
    species : varchar(64)
    date_of_birth : date
    """
