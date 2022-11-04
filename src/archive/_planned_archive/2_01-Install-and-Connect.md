

# Other Configuration Settings

If you are not using DataJoint on your own, or are setting up a
DataJoint system for other users, some additional configuraiton options
may be required to support `TLS <tls>` or `external storage <external>`
.

## TLS Configuration

Starting with v0.12 (Python) and v3.3.1 (MATLAB), DataJoint will by
default use TLS if it is available. TLS can be forced on or off with the
boolean `use_tls` in MATLAB, or `dj.config['database.use_tls']` in
Python.
