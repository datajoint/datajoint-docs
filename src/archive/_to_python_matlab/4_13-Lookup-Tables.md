---
title: Lookup Tables
---

Lookup tables are commonly populated from their `contents`
property. In an `ERD <erd>` they are shown in gray. The decision of
which tables are lookup tables and which are manual can be somewhat
arbitrary.

The table below is declared as a lookup table with its contents property
provided to generate entities.

=== "Python"

    ``` python
    @schema
    class User(dj.Lookup):
        definition = """
        # users in the lab
        username : varchar(20)   # user in the lab
        ---
        first_name  : varchar(20)   # user first name
        last_name   : varchar(20)   # user last name
        """
        contents = [
            ['cajal', 'Santiago', 'Cajal'],
            ['hubel', 'David', 'Hubel'],
            ['wiesel', 'Torsten', 'Wiesel']
    ]
    ```

=== "Matlab"

    File `+lab/User.m`

    ``` matlab
    %{
        # users in the lab
        username : varchar(20)   # user in the lab
        ---
        first_name  : varchar(20)   # user first name
        last_name   : varchar(20)   # user last name
    %}
    classdef User < dj.Lookup
        properties
            contents = {
                'cajal'  'Santiago' 'Cajal'
                'hubel'  'David'    'Hubel'
                'wiesel' 'Torsten'  'Wiesel'
            }
        end
    end
    ```

