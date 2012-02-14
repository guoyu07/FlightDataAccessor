import math
import shutil
import numpy as np
import h5py

def concat_hdf(hdf_paths, dest=None):
    '''
    Takes in a list of HDF file paths and concatenates the parameter
    datasets which match the path 'series/<Param Name>/data'. The first file
    in the list of paths is the template for the output file, with only the
    'series/<Param Name>/data' datasets being replaced with the concatenated
    versions.
    
    :param hdf_paths: File paths.
    :type hdf_paths: list of strings
    :param dest: optional destination path, which will be the first path in
                 'paths'
    :type dest: dict
    :return: path to concatenated hdf file.
    :rtype: str
    '''
    param_name_to_arrays = {}
    for hdf_path in hdf_paths:
        with h5py.File(hdf_path, 'r') as hdf_file:
            for param_name, param_group in hdf_file['series'].iteritems():
                try:
                    param_name_to_arrays[param_name].append(param_group['data'][:])
                except KeyError:
                    param_name_to_arrays[param_name] = [param_group['data'][:]]
    if dest:
        # Copy first file in hdf_paths so that the concatenated file includes
        # non-series data. XXX: Is there a simple way to do this with h5py?
        shutil.copy(hdf_paths[0], dest)
        
    else:
        dest = hdf_paths[0]
    with h5py.File(dest, 'r+') as dest_hdf_file:
        for param_name, array_list in param_name_to_arrays.iteritems():
            concat_array = np.concatenate(array_list)
            param_group = dest_hdf_file['series'][param_name]
            del param_group['data']
            param_group.create_dataset("data", data=concat_array, maxshape=(len(concat_array),))
    return dest


def strip_hdf(hdf_path, params_to_keep, dest):
    '''
    Strip an HDF file of all parameters apart from those in param_names. Does
    not raise an exception if any of the params_to_keep are not in the HDF file.
    
    :param hdf_path: file path of hdf file.
    :type hdf_path: str
    :param params_to_keep: parameter names to keep.
    :type param_to_keep: list of str
    :param dest: destination path for stripped output file
    :type dest: str
    :return: path to output hdf file containing specified segment.
    :rtype: str
    '''
    # Q: Is there a better way to clone the contents of an hdf file?
    shutil.copy(hdf_path, dest)
    with h5py.File(hdf_path, 'r+') as hdf_file:
        for param_name in hdf_file['series'].keys():
            if param_name not in params_to_keep:
                del hdf_file['series'][param_name]
    return dest
            


def write_segment(hdf_path, segment, dest):
    '''
    Writes a segment of the HDF file stored in hdf_path to dest defined by 
    segments, a slice in seconds. Expects the HDF file to contain whole
    superframes.
    
    Assumes "data" and "mask" are present.
    
    :param hdf_path: file path of hdf file.
    :type hdf_path: str
    :param segment: segment of flight to write in seconds. step is disregarded.
    :type segment: slice
    :param dest: destination path for output file containing segment.
    :type dest: str
    :return: path to output hdf file containing specified segment.
    :rtype: str
    
    TODO: Support segmenting parameter masks
    '''
    # Q: Is there a better way to clone the contents of an hdf file?
    shutil.copy(hdf_path, dest)
    param_name_to_array = {}
    duration = None
    if segment.start:
        supf_start_secs = (int(segment.start) / 64) * 64
        param_start_secs = (segment.start - supf_start_secs)
    if segment.stop:
        supf_stop_secs = ((int(segment.stop) / 64) * 64) + 64
        param_stop_secs = (supf_stop_secs - segment.stop)
        
    with h5py.File(hdf_path, 'r') as hdf_file:
        for param_name, param_group in hdf_file['series'].iteritems():
            data = param_group['data']
            mask = param_group['mask']
            frequency = param_group.attrs['frequency']
            # for params lower than 1hz, floor the start and round the top to take more than the required values
            if ((frequency * 64) % 1) != 0:
                raise ValueError("Parameter '%s' does not record a consistent "
                                 "number of values every superframe.",
                                 param_name)
            
            
            if segment.start:
                supf_start_index = int(supf_start_secs * frequency)
                param_start_index = int((segment.start - supf_start_secs) * frequency)
            else:
                supf_start_index = 0
                param_start_index = supf_start_index
            if segment.stop:
                supf_stop_index = int(supf_stop_secs * frequency)
                param_stop_index = int(segment.stop * frequency)
            else:
                supf_stop_index = len(data)
                param_stop_index = supf_stop_index
            
            segment_data = data[supf_start_index:supf_stop_index]
            segment_mask = mask[supf_start_index:supf_stop_index]
            # Mask data outside of split.
            segment_mask[:param_start_index] = True
            segment_mask[param_stop_index:] = True
            
            #supf_stop_index = len(param_group['data'])
            #start_index = math.floor(segment.start * frequency) if segment.start else 0
            ##TODO: Determine whether round or math.ceil is preferred option here:
            #if segment.stop:
                #stop_index = round(segment.stop * frequency)
                #if stop_index > len(param_group['data']):
                    ## TODO: Log?
                    #stop_index = len(param_group['data'])
            #else:
                #stop_index = len(param_group['data'])
            #seg_data = param_group['data'][int(start_index):int(stop_index)]
            #seg_mask = param_group['mask'][int(start_index):int(stop_index)]
            param_name_to_array[param_name] = (segment_data, segment_mask)
            if not duration and frequency == 1:
                duration = len(segment_data)
    with h5py.File(dest, 'r+') as hdf_file:
        for param_name, array in param_name_to_array.iteritems():
            param_group = hdf_file['series'][param_name]
            del param_group['data']
            param_group.create_dataset("data", data=array[0], maxshape=(len(array[0]),))
            del param_group['mask']
            param_group.create_dataset("mask", data=array[1], maxshape=(len(array[1]),))
        hdf_file.attrs['duration'] = duration
    return dest