# Sustainability Roadmap between DataJoint Elements and DANDI Archive

<figure markdown>
  ![datajoint](../../images/company-logo-black.svg){: style="height:50px; padding-right:25px"}
  ![dandi](../../images/community-partnerships-dandi-logo.png){: style="height:83px"}
</figure>

## Aim

**DataJoint Elements** and **The DANDI Archive (DANDI)** are two neuroinformatics
initiatives in active development. The projects develop independently yet they have
complementary aims and overlapping user communities. This document establishes key
processes for coordinating development and communications in order to promote
integration and interoperability across the two ecosystems.

## Projects and Teams

### DataJoint

**DataJoint Elements** — https://datajoint.com/docs/elements/ — is a collection of
  open-source reference database schemas and analysis workflows for neurophysiology
  experiments, supported by **DataJoint** — https://datajoint.com/docs/core/ — an
  open-source software framework. The project is funded by the NIH grant U24 NS116470
  and led by Dr. Dimitri Yatsenko.
  
The principal developer of DataJoint Elements and the DataJoint framework is the company
DataJoint — https://datajoint.com.

### Distributed Archives for Neurophysiology Data Integration (DANDI)

**DANDI** - https://dandiarchive.org — is an archive for neurophysiology data, 
providing neuroscientists with a common platform to share, archive, and process data. 
The project is funded by the NIH grant R24 MH117295 and led by Dr. Satrajit S. Ghosh 
and Dr. Yaroslav O. Halchenko.

The principal developers of DANDI are at the Massachusetts Institute of Technology, 
Dartmouth College, Catalyst Neuro, and Kitware.

## General Principles

### No obligation

The developers of the two ecosystems acknowledge that this roadmap document creates no 
contractual relationship between them but they agree to work together in the spirit of 
partnership to ensure that there is a united, visible, and responsive leadership and to 
demonstrate administrative and managerial commitment to coordinate development and 
communications.

### Coordinated Development

The two projects will coordinate their development approaches to ensure maximum
interoperability. This includes:

- coordinated use of terminology and nomenclatures
- support for testing infrastructure: unit testing and integration testing
- a coordinated software release process and versioning
- coordinated resolution of issues arising from joint use of the two tools

### Points of Contact

To achieve the aims of coordinated development, both projects appoint a primary point of
contact (POC) to respond to questions relating to the integration and interoperability 
of DataJoint Elements and DANDI.

For 2022, the DataJoint Elements POC is Dr. Kabilar Gunalan (kabilar@datajoint.com)

For 2022, the DANDI POC is Dr.Satrajit Ghosh (satra@mit.edu)

### Annual Review

To achieve the aims of coordinated development, the principal developers conduct a 
joint annual review of this roadmap document to ensure that the two programs are well 
integrated and not redundant. The contents and resolutions of the review will be made 
publicly available.

### Licensing

The two parties ensure that relevant software components are developed under licenses
that avoid any hindrance to integration and interoperability between DataJoint Elements
and DANDI.

## Development Roadmap

- [x] Mechanism to upload to DANDI - 
  [Element Interface DANDI module](https://github.com/datajoint/element-interface/blob/main/element_interface/dandi.py)

- [x] Documentation to upload to DANDI - 
  [Jupyter notebook](https://github.com/datajoint/workflow-array-ephys/blob/main/notebooks/09-NWB-export.ipynb)
