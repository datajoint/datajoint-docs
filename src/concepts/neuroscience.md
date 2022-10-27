# Neuroscience Concepts

Our DataJoint open-source initiative is supported by the NIH-U24 program. This allows the development and support for commonly used acquisition and analysis software in neuroscience research labs. An overview of commonly used tools for neuroscience experimental modalities are outlined below. 

## Array Electrophysiology

+ Acquisition:
  + [Neuropixels probes](https://www.neuropixels.org)
  + Tetrodes
  + [SpikeGLX](http://billkarsh.github.io/SpikeGLX/)
  + [OpenEphys](https://open-ephys.github.io/gui-docs/User-Manual/Plugins/Neuropixels-PXI.html)
  + [Neuralynx](https://neuralynx.com/)
  + [Axona](http://www.axona.com/)
  + ...

+ Analysis:
  + [Kilosort](https://github.com/MouseLand/Kilosort)
  + [pyKilosort](https://github.com/MouseLand/pykilosort)
  + [JRClust](https://github.com/JaneliaSciComp/JRCLUST)
  + [KlustaKwik](https://klusta.readthedocs.io/en/latest/)
  + [Mountainsort](https://github.com/flatironinstitute/mountainsort)
  + [spikeinterface (wrapper)](https://github.com/SpikeInterface)
  + [spyking-circus](https://github.com/spyking-circus/spyking-circus)
  + [spikeforest](https://spikeforest.flatironinstitute.org/)
  + ...

+ DataJoint Workflow Tools:
  + element-array-ephys: [https://github.com/datajoint/element-array-ephys](https://github.com/datajoint/element-array-ephys)
  + workflow-array-ephys: [https://github.com/datajoint/workflow-array-ephys](https://github.com/datajoint/workflow-array-ephys)

## Multi-photon Calcium Imaging

+ Biophysics of the acquisition methods:
  + [Kurt Thorn - YouTube](https://www.youtube.com/watch?v=CZifB2aQDDM)
  + [Dimitri Yatsenko - DataJoint Code Clinic](https://drive.google.com/file/d/1-xY340MhM-VPPmsxvPzoAFppylXLI3g5/view?usp=sharing)
  + [Biafra Ahanou blog](https://bahanonu.com/brain/#c20181209)

+ Analysis:
  + Suite2p:
    + [Marius Pachitariu - YouTube](https://www.youtube.com/user/mariuspach/featured)
    + [https://www.suite2p.org](https://www.suite2p.org)
    + [https://suite2p.readthedocs.io/en/latest/](https://www.suite2p.org)
  + [CaImAn](https://github.com/flatironinstitute/CaImAn)

+ DataJoint Workflow Tools:
  + element-calcium-imaging: [https://github.com/datajoint/element-calcium-imaging](https://github.com/datajoint/element-calcium-imaging)
  + workflow-calcium-imaging: [https://github.com/datajoint/workflow-calcium-imaging](https://github.com/datajoint/workflow-calcium-imaging)

## Miniscope Calcium Imaging

+ Acquisition:
  + [UCLA Miniscope](http://miniscope.org/index.php/Main_Page)
  + [Inscopix](https://www.inscopix.com)

+ Analysis:
  + [MiniAn](https://github.com/denisecailab/minian)
  + [Suite2p](https://github.com/MouseLand/suite2p)
  + [CaImAn](https://github.com/flatironinstitute/CaImAn)

+ DataJoint Workflow Tools:
  + element-miniscope: [https://github.com/datajoint/element-miniscope](https://github.com/datajoint/element-miniscope)
  + workflow-miniscope: [https://github.com/datajoint/workflow-miniscope](https://github.com/datajoint/workflow-miniscope)

## Sensory Stimulation

### Visual 
+ Example pipeline: [https://github.com/datajoint-catalog/djcat-visual-stimuli](https://github.com/datajoint-catalog/djcat-visual-stimuli)
+ Example pipeline: [https://github.com/datajoint-catalog/djcat-RET1](https://github.com/datajoint-catalog/djcat-RET1)
+ Allen Institute: [https://observatory.brain-map.org/visualcoding/](https://observatory.brain-map.org/visualcoding/)
+ odML - Terminologies: [http://portal.g-node.org/odml/terminologies/v1.0/stimulus/grating.xml](http://portal.g-node.org/odml/terminologies/v1.0/stimulus/grating.xml)


## Behavior Tracking

DeepLabCut (DLC) uses TensorFlow machine learning to estimate animal pose or pupillometry from (a) raw video data and (b) user-generated example frames. Typical uses include estimating the location of each ear and the tail base of a mouse to determine both where it was in a maze and the direction it was facing. 

The [repository](https://github.com/DeepLabCut/DeepLabCut) is maintained by Mackenzie Mathis’s team and is quickly becoming a standard in the field. The same process can be used for any species.

+ [DLC YouTube](https://www.youtube.com/channel/UC2HEbWpC_1v6i9RnDMy-dfA) covers installation and examples from the Mathis team.
+ DLC pipeline used in Mackenzie Mathis lab: https://github.com/MMathisLab/DataJoint_Demo_DeepLabCut
+ Existing DataJoint repository shows DLC within a workflow:
  + [https://github.com/datajoint-company/dj-imaging](https://github.com/datajoint-company/dj-imaging) (proprietary)

Treadmill data, including speed and direction, can show an animal’s activity during an experimental session. Head-fixed mice [can be trained](https://www.researchgate.net/publication/272381533_Acute_two-photon_imaging_of_the_neurovascular_unit_in_the_cortex_of_active_mice/figures?lo=1) to use a [spherical treadmill](https://sphericaltreadmill.com/spherical-treadmill-mice-small-animals.aspx) during calcium imaging, optionally with virtual reality [A](https://www.phenosys.com/products/virtual-reality/) & [B](https://www.youtube.com/watch?v=PHZytzVk4E0).

+ DataJoint Workflow Tools:
  + element-deeplabcut: [https://github.com/datajoint/element-deeplabcut](https://github.com/datajoint/element-deeplabcut)
  + workflow-deeplabcut: [https://github.com/datajoint/workflow-deeplabcut](https://github.com/datajoint/workflow-deeplabcut)

## Neurodata Without Borders (NWB) Data Standard

An nwb file is a highly-specified version of an H5DF file. [Schema docs](https://nwb-schema.readthedocs.io/) provide the relevant details for packaging neurobiology data into this format in both raw and processed forms. Generally, one nwb equates to one experimental session. 

While [H5DF has drawbacks](https://cyrille.rossant.net/moving-away-hdf5/), it is standardized across software/modalities. An nwb file can include raw and/or processed data from one experimental session.

DANDIArchive is a data archival service that prioritizes nwb submissions. Generally, one ‘dandiset’ is a series of nwbs that comprise an experiment.

[Ben Dichter](https://www.catalystneuro.com/team/) is closely involved with the development of NWB and DANDI. He has been contracted by DataJoint to write an electrophysiology export function, which DataJoint team members will parallel for other modalities. [Notes from Ben’s visit](https://docs.google.com/document/d/12CYzK8a4IDS6S_sVaImqPYP-fYyFrRQduNQJH5H7wZY/edit)

[NWB YouTube](https://www.youtube.com/c/NeurodataWithoutBorders) provides examples of use and integration with other tools. 

A functional NWB integrated DataJoint pipeline is developed by Loren Frank (FrankLab) at UCSF: [https://github.com/LorenFrankLab/nwb_datajoint](https://github.com/datajoint-company/dj-imaging)