# DataJoint Python Windows Install Guide

## Install PyDotPlus

The PyDotPlus library links the Graphviz installation to DataJoint and
is easily installed via `pip`:

![image](../_static/img/windows/install-pydotplus.png)

## Install Matplotlib

The Matplotlib library provides useful plotting utilities which are also
used by DataJoint's ERD drawing facility. The package is easily
installed via `pip`:

![image](../_static/img/windows/install-matplotlib.png)

# (Optional) step 5: install Jupyter Notebook

As described on [the jupyter.org website](http://jupyter.org):

> 'The Jupyter Notebook is an open-source web application that allows
> you to create and share documents that contain live code, equations,
> visualizations and narrative text.'

Although not a part of DataJoint, Jupyter Notebook can be a very useful
tool for building and interacting with DataJoint pipelines. It is easily
installed from `pip` as well:

![image](../_static/img/windows/install-jupyter-1.png)

![image](../_static/img/windows/install-jupyter-2.png)

Once installed, Jupyter Notebook can be started via the
`jupyter notebook` command, which should now be on your path:

![image](../_static/img/windows/verify-jupyter-install.png)

By default Jupyter Notebook will start a local private webserver session
from the directory where it was started and start a web browser session
connected to the session.

![image](../_static/img/windows/run-jupyter-1.png)

![image](../_static/img/windows/run-jupyter-2.png)

You now should be able to use the notebook viewer to navigate the
filesystem and to create new project folders and interactive
Jupyter/Python/DataJoint notebooks.

# Git for Windows

The [Git](https://git-scm.com/) version control system is not a part of
DataJoint but is recommended for interacting with the broader
Python/Git/GitHub sharing ecosystem.

The Git for Windows installer is available from
<https://git-scm.com/download/win>.

![image](../_static/img/windows/install-git-1.png)

The default settings should be sufficient and correct in most cases.
