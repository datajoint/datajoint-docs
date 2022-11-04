---
title: Manual Tables
---

The following code defines three manual tables `Animal`, `Session`, and
`Scan`:

=== "Python"

{{BEGIN INDENT}}

``` python
@schema
class Animal(dj.Manual):
    definition = """
    # information about animal
    animal_id : int  # animal id assigned by the lab
    ---
    -> Species
    date_of_birth=null : date  # YYYY-MM-DD optional
    sex='' : enum('M', 'F', '')   # leave empty if unspecified
    """

@schema
class Session(dj.Manual):
    definition = """
    # Experiment Session
    -> Animal
    session  : smallint  # session number for the animal
    ---
    session_date : date  # YYYY-MM-DD
    -> User
    -> Anesthesia
    -> Rig
    """

@schema
class Scan(dj.Manual):
    definition = """
    # Two-photon imaging scan
    -> Session
    scan : smallint  # scan number within the session
    ---
    -> Lens
    laser_wavelength : decimal(5,1)  # um
    laser_power      : decimal(4,1)  # mW
    """
```

{{END INDENT}}

=== "Matlab"

{{BEGIN INDENT}}

File `+experiment/Animal.m`

``` matlab
%{
  # information about animal
  animal_id : int  # animal id assigned by the lab
  ---
  -> experiment.Species
  date_of_birth=null : date  # YYYY-MM-DD optional
  sex='' : enum('M', 'F', '')   # leave empty if unspecified
%}
classdef Animal < dj.Manual
end
```

File `+experiment/Session.m`

``` matlab
%{
  # Experiment Session
  -> experiment.Animal
  session  : smallint  # session number for the animal
  ---
  session_date : date  # YYYY-MM-DD
  -> experiment.User
  -> experiment.Anesthesia
  -> experiment.Rig
%}
classdef Session < dj.Manual
end
```

File `+experiment/Scan.m`

``` matlab
%{
  # Two-photon imaging scan
  -> experiment.Session
  scan : smallint  # scan number within the session
  ---
  -> experiment.Lens
  laser_wavelength : decimal(5,1)  # um
  laser_power      : decimal(4,1)  # mW
%}
classdef Scan < dj.Manual
end
```

{{END INDENT}}
