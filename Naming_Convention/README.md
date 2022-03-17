# Overall steps to upload data to repository
1. For data to be uploaded, ensure that the structure of the directories containing the data as well as the naming of the directories and files comply with that specified in **"Structure"** and **"Naming"** sections below. This can be either done manually or/and with the help of **rename_parser_script.py** provided in this repository.
2. Follow steps detailed in **"Upload"** section below to move data to the CKAN server and upload to the ATB repository


# Structure
Each directory contains inputs, outputs, and other important files from the simulation. The below is an example, but not all of these folder/outputs are enforced (see FAQ) 

```
└──System_Name
(Master directory containing subdirectories for different types of data, name can be a descriptor of the system simulated)
    ├── atbrepo.yml
    (file containing metadata for the system, see section **atbrepo.yml** below for details)
    ├── control
    (Simulation control file, e.g. .mdp file for GROMACS; .imd file for GROMOS, .mdin for AMBER)
    ├── energy
    (Energy trajectory files)
    ├── final-coordinates
    (Output coordinate files from the simulations)
    ├── input-coordinates
    (Input coordinate files for the simulations)
    ├── forcefield-files
    (Forcefield files, e.g. .ifp file for GROMACS; .itp files for GROMOS)
    ├── log
    (Simulation log files)
    ├── reference-coordinates
    (Coordinate files relevant to the simulation that is not the the input or output coordinates for the simulations)
    ├── topology
    (Topology files of the simulated system)
    └── trajectory
    (Coordinate trajectory files for the simulation)
   ```

-------------------------------------------------------
# atbrepo.yml
atbrepo.yml is a file containing metadata for the system.

The information includes:
- **title:** This will appear as the title of the simulation on the website.
- **notes:** This will appear as a description of the simulation on the website.
- **program:** A list of MD programs. Of course we would expect only one, but because of the way we implemented a special program tag in CKAN, it makes it easier to include this in atbrepo.yml as a list.
- **organization:** The organisation the system is affiliated with as per the organisation URL
- **tags:** Freeform text tags for the simulation. Note that some tags are prefixed with ‘item-’, namely:
    - *replicate*-[number] of [total number]
    - *protein*-[name of protein]
    - *peptide*-[name of peptide]
    - *lipid*-[name of lipid]
    - *PDB*-[pdb code]
    - *solvent*-[name of solvent]


Here are some example metadata files:

Lipid bilayer in Gromacs: 
    `/home/atb/atb_repo/trajectory_data/tlee/TL_bilayer/TL_bilayer_D6PC_H2O_512_303K/atbrepo.yml`
```
notes: A lipid bilayer consisting of 512 D6PC molecules. Initiated from a smaller
  128-lipid DLPC equilibrated bilayer with trimmed tails. Pore spontaneously form
  during the simulation.
program: GROMACS
tags:
- lipid-D6PC
- lipid bilayer
- GROMOS
- 54A7
- solvent-H2O
organization: mduq
title: D6PC lipid bilayer
```

Protein in Amber: 
    `/home/atb/atb_repo/trajectory_data/GROMOS_54A7_AMBER_Validation/1aki_54a7_amber_rep_1/atbrepo.yml`

```
notes: 'Hen egg-white lysozyme protein with GROMOS 54A7 in AMBER (replicate 1 of 3).
  Initial structure obtained from the Protein Data Bank (PDB). PDB ID: 1AKI, URL:
  <a href="https://www.rcsb.org/structure/1AKI">https://www.rcsb.org/structure/1AKI</a>'
program:
- AMBER
tags:
- GROMOS
- 54A7
- solvent-H2O
- replicate-1 of 3
- PDB-1AKI
- protein-hen egg-white lysozyme
- protein
organization: mduq
title: Hen egg-white lysozyme
```

Peptide in Gromos: 
    `/home/atb/atb_repo/trajectory_data/GROMOS_54A7_Validation/ap_54a7_rep_1/atbrepo.yml`

```
notes: Alpha-helical peptide AP with GROMOS 54A7 in GROMOS (replicate 1 of 3).
program:
- GROMOS
tags:
- GROMOS
- 54A7
- solvent-H2O
- replicate-1 of 3
- peptide-alpha-helical peptide AP
- peptide
organization: mduq
title: Alpha-helical peptide AP
```

-------------------------------------------------------
# Naming
Within each subdirectory, the files are named as follows:
    `<simulation_name>_<file-category>_<run-number>.<file-extension>`

Using the above example for a control file in GROMACS: 
    `System_Name_control_00001.mdp`

-------------------------------------------------------
# Upload
To do this, you will need an account on `scmb-ckan.research.dc.uq.edu.au` with sudo permissions.

To start, rsync your files to `scmb-ckan.research.dc.uq.edu.au:/Q0289/pending_atb_repo_data/<YOUR_NAME>`. You will need to make the folder with your name. It's important that your files have read permissions for everyone, so make sure to double check that once you have done the rsync.

Make a folder inside `/Q0289/atb_repo_data` with your name, this is important so we can track who uploaded what data.

Move each system one at a time to your folder `/Q0289/atb_repo_data/<YOUR_NAME>`, and each time run the upload script on each new folder. It's important you do this one at a time incase there are upload problems. ONLY uploaded data should be inside the `atb_repo_data` folder. The upload script is located in `/home/atb/atb_repo/atbr_updater`. The current iteration of the script is called `update_https_orgs_comments.py`. To run the script, run the following command:
    `sudo python3 update_https_orgs_comments.py -d /home/atb/atb_repo/trajectory_data/<YOUR_NAME>/<your_system_name>`

If there are problems, you will recieve errors when you run the script. If you have implimented your files correctly, you will recieve no errors and the system will be visable on the repository web server. It's worthwhile to double check you can access the files successfully on the web server before you continue to upload. If you need to update a system, you can rerun the above command on the same folder and the details will be updated in the repository.

-------------------------------------------------------
# FAQs
*Which directories/ files are enforced?* control, log, topology

*Which directories have an enforces naming style?* control, coordinates, energy, final-coordinates, input-coordinates, log, trajectory

*What information in atbrepo.yml is enforced?*

*Is there any way of linking different entries I submitted? For example, different repeat runs of the the same system*




