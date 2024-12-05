"""Package the project"""

from setuptools import find_packages, setup

setup(
    name="gds_checker",
    version="0.1.0",
    description=(
        "Python software aiming to check that GHRSST products have a"
        "standard format, specified by the GHRSST Data "
        "Specification"
    ),
    author="Nathan Lalloué",
    author_email="Nathan.lalloue@noveltis.fr",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "gds_checker": ["*.yml"],
    },
    install_requires=["netcdf4", "pyyaml", "xarray"],
    classifiers=[
        "Programming Language :: Python",
    ],
    entry_points={
        "console_scripts": [
            "gds_checker = gds_checker.gds_checker:main",
        ],
    },
)
