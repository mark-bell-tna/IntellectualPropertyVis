# Instructions for loading data

Each script loads a different type of data for a year. The data is held in zip files in the Data folder, which will need to be unzipped prior to loading.

The BT_43_metadata_to_graph.py should be run first as it loads the 'spine' of the data, i.e. catalogue references. The others are independent of each other.
One approach may be to load a single year for each data type, and then test the visualisations. Another approach would be load all of the metadata and then incrementally add the other data types. To load all years, simply create a loop at the command line passing each year in turn as a parameter.
The date visualisation requires only the basic metadata at a minimum, although other data is needed to get value from the interactive elements. The other graphs all require the full set of data types for each year.

## Suggested loading process for 1872:

1. BT_43_metadata_to_graph.py 1872
2. BT_43_date_graph.py 1872  (this is needed if single year visualisations are required)
3. BT_43_proprietors_to_graph.py 1872  (full functionality of data graph available after this)
4. BT_43_addresses_to_graph.py 1872
5. BT_43_classes_to_graph.py 1872   (by place graph will work after these two have run)
6. BT_43_subjects_to_graph.py 1872
