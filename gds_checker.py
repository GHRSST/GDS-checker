import sys
import re
import os
import yaml
import xarray as xr
import numpy as np

def load_config(config_file):
    
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def construct_pattern(config):

    processing_levels = '|'.join(config['file_naming_conventions']['processing_levels'])
    rdacs = '|'.join(config['file_naming_conventions']['rdacs'])
    sst_types = '|'.join(config['file_naming_conventions']['sst_types'])
    file_types = '|'.join(config['file_naming_conventions']['file_types'])
                  
    pattern = fr'^(\d{{8}})(\d{{6}})-({rdacs})-({processing_levels})_GHRSST-({sst_types})-(\w+)-(\w+)-v(\d+\.\d+)-fv(\d+\.\d+)\.({file_types})$'
    
    return pattern

def check_file_name(file_name, pattern):
    
    match = re.match(pattern, file_name)
    if match is None:
        print("File name does not follow the naming convention.")
    return 
    
def check_global_attributes(ds, config):
        
    for global_attribute in config['global_attributes']:
                
        global_attribute_name = list(global_attribute.keys())[0]
                
        expected_types = global_attribute[global_attribute_name]['types']
        
        if global_attribute_name not in ds.attrs:
            if global_attribute[global_attribute_name]['mandatory'] == True:
                print(f"Global attribute '{global_attribute_name}' does not exist in the NetCDF file, and is mandatory")
            else:
                print(f"Global attribute '{global_attribute_name}' does not exist in the NetCDF file, but is not mandatory")
            continue
        
        actual_type = type(ds.attrs[global_attribute_name])
        
        i = 0
        for expected_type in expected_types:
            if actual_type == np.dtype(expected_type):
                i = i + 1
                break
        if i<1:
            print(f"Global attribute '{global_attribute_name}' has type '{actual_type}', expected types '{expected_types}'.")
                    
        if "allowed_values" in global_attribute[global_attribute_name]:
                
                allowed_values = global_attribute[global_attribute_name]['allowed_values']
                
                i = 0
                for allowed_value in allowed_values:
                    if ds.attrs[global_attribute_name] == allowed_value:
                        i = i + 1
                        break
                if i<1:
                    print(f"Global attribute '{global_attribute_name}' has value '{ds.attrs[global_attribute_name]}', allowed values '{allowed_values}'.")

def check_variables(ds, config):
    
    for variable in config['variables']:
        
        variable_name = list(variable.keys())[0]
                
        expected_types = variable[variable_name]['types']
        
        if variable_name not in ds.variables:
            if variable[variable_name]['mandatory'] == True:
                print(f"Variable '{variable_name}' does not exist in the NetCDF file, and is mandatory")
            else:
                print(f"Variable '{variable_name}' does not exist in the NetCDF file, but is not mandatory.")
            continue
        
        variable_DataArray = ds[variable_name]
        actual_type = variable_DataArray.dtype  
        
        i = 0
        for expected_type in expected_types:
            if actual_type == np.dtype(expected_type):
                i = i + 1
                break
        if i<1:
            print(f"Variable '{variable_name}' has type '{actual_type}', expected types '{expected_types}'.")
                            
        for attribute in variable[variable_name]['attributes']:
            
            attribute_name = list(attribute.keys())[0]
            
            if attribute_name not in variable_DataArray.attrs:
                if attribute[attribute_name]['mandatory'] == True:
                    print(f"Variable attribute '{attribute_name}' does not exist for the variable '{variable_name}', and is mandatory")
                else:
                    print(f"Variable attribute '{attribute_name}' does not exist for the variable '{variable_name}', but is not mandatory")
                continue
            
            actual_type = type(variable_DataArray.attrs[attribute_name])
            expected_types = attribute[attribute_name]['types']
            
            i = 0
            for expected_type in expected_types:
                if actual_type == np.dtype(expected_type):
                    i = i + 1
                    break
            if i<1:
                print(f"Variable attribute '{attribute_name}' for the variable '{variable_name}' has type '{actual_type}', expected types '{expected_types}'.")
                
            if "allowed_values" in attribute[attribute_name]:
                
                allowed_values = attribute[attribute_name]['allowed_values']
                
                i = 0
                for allowed_value in allowed_values:
                    if variable_DataArray.attrs[attribute_name] == allowed_value:
                        i = i + 1
                        break
                if i<1:
                    print(f"Variable attribute '{attribute_name}' for the variable '{variable_name}' has value '{variable_DataArray.attrs[attribute_name]}', allowed values '{allowed_values}'.")
                

def check_lon_lat_time_missing_values(ds):
    
    if not 'lon' in ds.coords:
        print("The dataset does not contain the 'lon' coordinate")
        return
    
    longitude_values = ds.lon.values
    are_lon_nan = np.isnan(longitude_values).any()
    if are_lon_nan:
        print(f"There are NaNs in the longitude array")
    
    if not 'lat' in ds.coords:
        print("The dataset does not contain the 'lat' coordinate")
        return
    
    latitude_values = ds.lat.values
    are_lat_nan = np.isnan(latitude_values).any()
    if are_lat_nan:
        print(f"There are NaNs in the latitude array")
    
    if not 'time' in ds.coords:
        print("The dataset does not contain the 'time' coordinate")
        return
    
    time_values = ds.time.values
    are_time_nan = np.isnan(time_values).any()
    if are_time_nan:
        print(f"There are NaNs in the time array")
    
    return

def check_lon_boundaries(ds, config):
    
    valid_min = config['longitude']['valid_min']
    valid_max = config['longitude']['valid_max']
    
    if not 'lon' in ds.coords:
        print("The dataset does not contain the 'lon' coordinate")
        return
        
    longitude_values = ds.lon.values
    are_within_range = np.all((longitude_values >= valid_min) & (longitude_values <= valid_max))
    
    if not are_within_range:
        print(f"Some longitudes are outside the range {valid_min} to {valid_max}.")
        
    return
    
if __name__ == "__main__":
    
    if len(sys.argv) != 3:
        print("Usage: python gds_checker.py <netcdf_file_path> config.yml")
        sys.exit(1)

    file_path = sys.argv[1]
    config_file = sys.argv[2]
    
    config = load_config(config_file)
    
    pattern = construct_pattern(config)
    
    file_name = os.path.basename(file_path)
    
    check_file_name(file_name, pattern)
    
    with xr.open_dataset(file_path) as ds:
        check_global_attributes(ds, config)
        check_variables(ds, config)
        check_lon_lat_time_missing_values(ds)
        check_lon_boundaries(ds, config) 