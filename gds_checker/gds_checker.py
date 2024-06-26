"""Python software aiming to check that GHRSST products have a standard format,
specified by the GHRSST Data Specification."""

import sys
import re
import os
import logging
import argparse
import yaml
import xarray as xr
import numpy as np

PROGRAM_VERSION = "0.1.0"

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)-10s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def load_config(config_file: str) -> dict:
    """
    Function to load a configuration file

    Args:
        config_file (str): path to the configuration file
    """
    with open(config_file, 'r', encoding="utf-8") as f:
        return yaml.safe_load(f)


def construct_pattern(config: dict) -> str:
    """
    Function to construct a pattern from
    a configuration file

    Args:
        config (dic): Configuration file
    """
    processing_levels = '|'.join(config
                                 ['file_naming_conventions']
                                 ['processing_levels']
                                 )
    rdacs = '|'.join(config['file_naming_conventions']
                     ['rdacs']
                     )
    sst_types = '|'.join(config['file_naming_conventions']
                         ['sst_types']
                         )
    file_types = '|'.join(config['file_naming_conventions']
                          ['file_types']
                          )
    pattern = fr'^(\d{{8}})(\d{{6}})-({rdacs})-({processing_levels})_' \
              fr'GHRSST-({sst_types})-(\w+)-(\w+)-v(\d+\.\d+)-fv(\d+\.\d+)\.' \
              fr'({file_types})$'
    return pattern


def check_file_name(file_name: str,
                    pattern: str) -> re.Match | None:
    """
    Function to check if the file name follows
    the pattern

    Args:
        file_name (str): input file name
        pattern (str): pattern to be followed
    """
    logger.info("Checking file naming...")
    logger.info("-----------------------")
    match = re.match(pattern, file_name)
    if match is None:
        logger.critical("    File name does not follow the naming convention. Can't check the variables.")
        print(" ")
        return None
    else:
        logger.info("    File name is ok.")
        print(" ")
        return match


def check_global_attributes(ds: xr.Dataset,
                            config: dict) -> None:
    """
    Function to check the global_ attributes inside the file,
    given the corresponding configuration file

    Args:
        ds (xr.Dataset): input Dataset
        config (dict): corresponding configuration file
    """
    count = 0
    logger.info("Checking global attributes...")
    logger.info("-----------------------------")
    for global_attribute in config['global_attributes']:
        global_attribute_name = list(global_attribute.keys())[0]
        if global_attribute_name not in ds.attrs:
            if 'mandatory' in global_attribute[global_attribute_name]:
                if global_attribute[global_attribute_name]['mandatory'] is True:
                    logger.error("    Global attribute: '%s' missing.",
                                 global_attribute_name)
                    count = count + 1
                else:
                    logger.warning("    Global attribute: '%s' missing.",
                                   global_attribute_name)
                    count = count + 1
                continue
            else:
                logger.error("    Global attribute: '%s' missing.",
                             global_attribute_name)
                count = count + 1
                continue
        else:
            if 'deprecated' in global_attribute[global_attribute_name]:
                if (global_attribute[global_attribute_name]['deprecated'] is True):
                    logger.warning("    Global attribute: '%s' deprecated.",
                                   global_attribute_name)
                    count = count + 1
                    continue
        actual_type = type(ds.attrs[global_attribute_name])
        expected_types = global_attribute[global_attribute_name][
            'allowed_types']
        i = 0
        for expected_type in expected_types:
            if actual_type == np.dtype(expected_type):
                i = i + 1
                break
        if i < 1:
            logger.error("    Global attribute: '%s' has type: '%s', allowed types: '%s'.",
                         global_attribute_name, actual_type, expected_types)
            count = count + 1
        if "allowed_values" in global_attribute[global_attribute_name]:
            allowed_values = global_attribute[global_attribute_name][
                'allowed_values']
            i = 0
            for allowed_value in allowed_values:
                if ds.attrs[global_attribute_name] == allowed_value:
                    i = i + 1
                    break
            if i < 1:
                logger.error("    Global attribute: '%s' has value: '%s', allowed values: '%s'.",
                             global_attribute_name,
                             ds.attrs[global_attribute_name],
                             allowed_values)
                count = count + 1
    if count == 0:
        logger.info("    Global attributes are ok.")
        print(" ")
    else:
        print(" ")
    return


def check_variables(ds: xr.Dataset,
                    config: dict) -> None:
    """
    Function to check the variables inside the file,
    given the corresponding configuration file

    Args:
        ds (xr.Dataset): input Dataset
        config (dict): corresponding configuration file
    """
    count = 0
    logger.info("Checking variables...")
    logger.info("---------------------")
    for variable in config['variables']:
        variable_name = list(variable.keys())[0]
        expected_types = variable[variable_name]['allowed_types']
        if variable_name not in ds.variables:
            if 'mandatory' in variable[variable_name]:
                if variable[variable_name]['mandatory'] is True:
                    logger.error("    Variable: '%s' missing.",
                                 variable_name)
                    count = count + 1
                else:
                    logger.warning("    Variable: '%s' missing.",
                                   variable_name)
                    count = count + 1
                continue
            else:
                logger.error("    Variable: '%s' missing.",
                             variable_name)
                count = count + 1
                continue
        variable_data_array = ds[variable_name]
        actual_type = variable_data_array.dtype
        i = 0
        for expected_type in expected_types:
            if actual_type == np.dtype(expected_type):
                i = i + 1
                break
        if i < 1:
            logger.error("    Variable: '%s' has type: '%s', allowed types: '%s'.",
                         variable_name, actual_type, expected_types)
            count = count + 1
        for attribute in variable[variable_name]['attributes']:
            attribute_name = list(attribute.keys())[0]
            if attribute_name not in variable_data_array.attrs:
                if 'mandatory' in attribute[attribute_name]:
                    if attribute[attribute_name]['mandatory'] is True:
                        logger.error("    Variable attribute: '%s' missing for the variable: '%s'.",
                                     attribute_name, variable_name)
                        count = count + 1
                    else:
                        logger.warning("    Variable attribute: '%s' missing for the variable: '%s'.",
                                       attribute_name, variable_name)
                        count = count + 1
                    continue
                else:
                    logger.error("    Variable attribute: '%s' missing for the variable: '%s'.",
                                 attribute_name, variable_name)
                    count = count + 1
                    continue
            actual_type = type(variable_data_array.attrs[attribute_name])
            expected_types = attribute[attribute_name]['allowed_types']
            i = 0
            for expected_type in expected_types:
                if actual_type == np.dtype(expected_type):
                    i = i + 1
                    break
            if i < 1:
                logger.error("    Variable attribute: '%s' for the variable: '%s' has type: %s, allowed types: %s.",
                             attribute_name, variable_name, actual_type, expected_types)
                count = count + 1
            if "allowed_values" in attribute[attribute_name]:
                allowed_values = attribute[attribute_name]['allowed_values']
                i = 0
                for allowed_value in allowed_values:
                    if variable_data_array.attrs[attribute_name] == \
                            allowed_value:
                        i = i + 1
                        break
                if i < 1:
                    logger.error("    Variable attribute: '%s' for the variable: '%s' has value: '%s',  allowed values: %s.",
                                 attribute_name, variable_name, variable_data_array.attrs[attribute_name],
                                 allowed_values)
                    count = count + 1
    if count == 0:
        logger.info("    Variables are ok.")
        print(" ")
    else:
        print(" ")
    return


def check_undefined_lon_lat_time(ds: xr.Dataset) -> None:
    """
    Function to check if the longitude,
    latitude and time varibales of the Dataset
    contain undefined values

    Args:
        ds (xr.Dataset): input Dataset
    """
    count = 0
    logger.info("Checking undefined lon, lat and time...")
    logger.info("---------------------------------------")
    if 'lon' not in ds.coords:
        logger.error("    'lon' coordinate missing.")
        count = count + 1
    else:
        longitudes = ds.lon
        if longitudes.count() != longitudes.size:
            logger.error("    Undefined lon values.")
            count = count + 1
    if 'lat' not in ds.coords:
        logger.error("    'lat' coordinate missing.")
        count = count + 1
    else:
        latitudes = ds.lat
        if latitudes.count() != latitudes.size:
            logger.error("    Undefined lat values.")
            count = count + 1
    if 'time' not in ds.coords:
        logger.error("    'time' coordinate missing.")
        count = count + 1
    else:
        time = ds.time
        if time.count() != time.size:
            logger.error("    Undefined time values.")
            count = count + 1
    if count == 0:
        logger.info("    Lon, lat and time are ok.")
        print(" ")
    else:
        print(" ")
    return


def check_lon_boundaries(ds: xr.Dataset,
                         config: dict) -> None:
    """
    Function to check if the longitude,
    latitude and time varibales of the Dataset
    contain Nans

    Args:
        ds (xr.Dataset): input Dataset
        config (dict): configuration file
    """
    count = 0
    valid_min = config['longitude']['valid_min']
    valid_max = config['longitude']['valid_max']
    logger.info("Checking lon between %s and %s...", valid_min, valid_max)
    logger.info("------------------------------------")
    if 'lon' not in ds.coords:
        logger.error("    'lon' coordinate missing.")
        count = count + 1
    else:
        longitude_values = ds.lon.values
        are_within_range = np.all(
            (longitude_values >= valid_min) & (longitude_values <= valid_max)
        )
        if not are_within_range:
            logger.error("    Lon NOT between %s and %s.",
                         valid_min, valid_max)
            count = count + 1
    if count == 0:
        logger.info("    Lon between %s and %s.", valid_min, valid_max)
        print(" ")
    else:
        print(" ")
    return


def main():
    """
    Main function to run the script

    Args:
    """
    parser = argparse.ArgumentParser(usage='%(prog)s <netcdf_file_path>',
                                     epilog="Example: %(prog)s test.nc")
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s v{PROGRAM_VERSION}')
    _, unknown = parser.parse_known_args()
    if len(unknown) != 1:
        parser.error("Usage: gds_checker <netcdf_file_path>")
    file_path = unknown[0]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.yml')
    config = load_config(config_path)
    pattern = construct_pattern(config)
    file_name = os.path.basename(file_path)
    match = check_file_name(file_name, pattern)
    if not os.path.isfile(file_path):
        logger.critical("File: %s does not exist", file_path)
        sys.exit(1)
    with xr.open_dataset(file_path, decode_cf=False,
                         decode_times=False,
                         decode_timedelta=False) as ds:
        check_global_attributes(ds, config)
        processing_level = None
        if "processing_level" in ds.attrs:
            processing_level = ds.attrs["processing_level"]
            if match is not None:
                processing_level_file_name = match.group(4)
                if processing_level != processing_level_file_name:
                    logger.error("    Processing level is not the same in file name and in attribute. Taking the attribute"
                                 " one for checking the variables.")
        else:
            logger.warning("    Attribute 'processing_level' not found. Checking the file name.")
            if match is not None:
                processing_level = match.group(4)
        if processing_level is not None:
            processing_level_config_path = os.path.join(
                script_dir, processing_level + ".yml"
            )
            processing_level_config = load_config(processing_level_config_path)
            check_variables(ds, processing_level_config)
        else:
            logger.error("    Processing level not found neither in file name nor as attribute. Can't check the variables")
    with xr.open_dataset(file_path) as ds:
        check_undefined_lon_lat_time(ds)
        check_lon_boundaries(ds, config)


if __name__ == "__main__":
    main()
