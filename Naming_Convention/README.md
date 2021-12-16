# Structure

```
└── System_Name
    ├── atbrepo.yml
    ├── control
    ├── energy
    ├── final-coordinates
    ├── input-coordinates
    ├── itp-files
    ├── log
    ├── reference-coordinates
    ├── topology
    └── trajectory
   ```

-------------------------------------------------------
# atbrepo.yml
\\ atbrepo.yml is a file containing metadata for the system.

The information includes:
- **title:** This will appear as the title of the simulation on the website.
- **notes:** This will appear as a description of the simulation on the website.
- **program:** A list of MD programs. Of course we would expect only one, but because of the way we implemented a special program tag in CKAN, it makes it easier to include this in atbrepo.yml as a list.
- **tags:** Freeform text tags for the simulation. Note that some tags are prefixed with ‘item-’, namely:
    - *replicate*-[number] of [total number]
    - *protein*-[name of protein]
    - *peptide*-[name of peptide]
    - *lipid*-[name of lipid]
    - *PDB*-[pdb code]
    - *solvent*-[name of solvent]


Here are some example metadata files:

Lipid bilayer in Gromacs: 
    /home/atb/atb_repo/trajectory_data/tlee/TL_bilayer/TL_bilayer_D6PC_H2O_512_303K/atbrepo.yml
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
title: D6PC lipid bilayer
```

Protein in Amber: 
    /home/atb/atb_repo/trajectory_data/GROMOS_54A7_AMBER_Validation/1aki_54a7_amber_rep_1/atbrepo.yml

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
title: Hen egg-white lysozyme
```

Peptide in Gromos: 
    /home/atb/atb_repo/trajectory_data/GROMOS_54A7_Validation/ap_54a7_rep_1/atbrepo.yml

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
title: Alpha-helical peptide AP
```

-------------------------------------------------------
# Naming
\\Each directory contains inputs, outputs, and other important files from the simulation. The above is an example, but not all of these folder/outputs are enforced. Within each folder, the files are named as follows:
    > simulation_name_file-category_Run#.extension

\\Using the above example for a control file in GROMACS: 
    > System_Name_control_00001.mdp

-------------------------------------------------------
# FAQs
\\ *Which directories/ files are enforced?* control, log, topology
\\ *Which directories have an enforces naming style?* control, coordinates, energy, final-coordinates, input-coordinates, log, trajectory


