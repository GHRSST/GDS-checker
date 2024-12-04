# GDS checker

```
This software is available under the GPLv3 license.

This work was funded by the European Union's Copernicus programme as part of the contractual activities Sci4Mast conducted by a consortium led by NOVELTIS, under EUMETSAT Contract No. EUM/CO/21/46000021047/AOC.

© European Union’s Copernicus programme. 
```

``GDS checker`` is a Python software aiming to check that GHRSST products have a standard format, specified by the GHRSST Data Specification (GDS) (see: [The Recommended GHRSST Data Specification (GDS)](https://zenodo.org/records/6984989)).

## Requirements

``GDS checker`` requires:

- [Python](https://www.python.org/)
- [Git](https://git-scm.com/)

## Installation

``GDS checker`` can be installed with:

```bash
git clone https://github.com/GHRSST/GDS-checker.git
cd GDS-checker

pip install .
```

## Usage

``GDS checker`` can be used with:

```bash
gds_checker <netcdf_file_path>
```
