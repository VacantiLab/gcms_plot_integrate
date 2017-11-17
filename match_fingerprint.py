def match_fingerprint(ri_array,coelut_dict,coelut_dict_val,metabolite_dict,mz_vals):
    import numpy as np
    import importlib
    import pdb
    import find_closest
    importlib.reload(find_closest)

    #find the mz index range of the scan
    mz_scan_start = mz_vals[0]
    mz_scan_end = mz_vals[len(mz_vals)-1]

    #specify the metabolite - will be done as input to the function later
    metabolite = 'lactate'

    #determine the metabolite fingerprint array
    metabolite_peak_profile = metabolite_dict[metabolite]['peak_profile']

    #convert the peak profile stored in the library into the metabolite fingerprint dictionary used by this function
    fingerprint = dict()
    for item in metabolite_peak_profile:
        if item > 1:
            fingerprint[item] = np.array([])
            current_key = item
        if item <= 1:
            fingerprint[current_key] = np.append(fingerprint[current_key],item)

    #trim the peak profile so that entries outiside of the mz scan range are not considered in the match
    fingerprint = trim_peak_profile(fingerprint,mz_scan_start,mz_scan_end)

    #define the retention index of the metabolite as found in the library
    metabolite_ri = 1388

    #define the window around the library retention index the metabolite is allowed to be found
    ri_window = 5
    ri_upper = metabolite_ri + ri_window
    ri_lower = metabolite_ri - ri_window

    #find the indices within the retention index array that border this retention index window
    metabolite_ri_ind,metabolite_ri = find_closest.find_closest(metabolite_ri,ri_array)
    ri_upper_ind,ri_upper = find_closest.find_closest(ri_upper,ri_array)
    ri_lower_ind,ri_lower = find_closest.find_closest(ri_lower,ri_array)

    #initialize a dictionary where the key value will be the mz groups (keys of fingerprint)
    #    the values for each key will be the retention indices where all mzs within that group are present
    metabolite_elut_ri_dict = dict()

    #get a list of the mz values heading each defined group of mz values
    group_mz_list = list(dict.keys(fingerprint))

    #initialize the values for each key of metabolite_elut_ri_dict to be an empty np array
    for mz in group_mz_list:
        metabolite_elut_ri_dict[mz] = np.array([])

    #iterate through the retention indices of the defined window
    #    at each retention index, the coeluting peaks are examined
    #    the set of coeluting peaks is tested against each group of mz values
    #    for each group of mz values, the retention indices where all members of the group of mz values are in the coeluting peaks is recoreded
    for i in range(ri_lower_ind,ri_upper_ind+1):
        ri = ri_array[i]
        peak_mz_array = coelut_dict[ri]
        peak_val_array = coelut_dict_val[ri]
        for mz in group_mz_list:
            n_mz = len(fingerprint[mz])
            mz_in_group = np.arange(mz,mz+n_mz)
            lib_in_samp_ind = np.isin(mz_in_group,peak_mz_array)
            lib_in_samp = np.all(lib_in_samp_ind)
            if lib_in_samp:
                metabolite_elut_ri_dict[mz] = np.append(metabolite_elut_ri_dict[mz],ri)
                #for each group of mz values, the key name is the first mz
                #the ri's where all members of the group are eluting is recorded

    #find the retention indices where all groups are present
    j = 0
    for mz in group_mz_list:
        if j==0:
            intersection = metabolite_elut_ri_dict[mz]
        if not j==0:
            intersection = np.intersect1d(intersection,metabolite_elut_ri_dict[mz])
        j = j+1

    #report if the metabolite is present and if so, what its observed retention index is
    metabolite_present = False
    metabolite_retention_index = 0
    if len(intersection) > 0:
        metabolite_present = True
        metabolite_retention_index = np.median(intersection)

    pdb.set_trace()

    return(metabolite_present,metabolite_retention_index)

#Supporting Functions##############################
def trim_peak_profile(fingerprint,mz_scan_start,mz_scan_end):

    #retrieve a list of all mz values beginning a group
    group_mz_list = list(dict.keys(fingerprint))

    #iterate througn those values
    for mz in group_mz_list:
        #if you find an mz value beginning a group that is smaller than the smallest mz value scanned, examine it further
        if mz < mz_scan_start:
            group_mz = fingerpring[mz] #retrieve an array of all of the mz values in that group
            n_group_mz = len(group_mz) #retrieve the number of mz values in that group
            #iterate through each individual value in that group
            for i in np.arange(0,n_group_mz):
                #keep track of the number of values that must be removed (those less than the first mz value scanned)
                remove_count = 0
                if mz+i < mz_scan_start:
                    remove_count = remove_count + 1
            #remove the values corresponding to thouse found to be smaller than the smallest value scnaned
            indices_to_delete = np.range(0,remove_count)
            group_mz = np.delete(group_mz,indices_to_delete)
            #update the dicionary key entry appropriately
            if len(group_mz) == 0: #remove the key entirely if it corresponds to an empty array
                fingerprint[mz] = fingerprint.pop[mz,None]
            if len(group_mz) > 0: #rename the entry after the smallest (first) value
                new_key = group_mz[0]
                fingerprint[new_key] = fingerprint.pop[mz]
    return(fingerprint)

    return(c_var)
