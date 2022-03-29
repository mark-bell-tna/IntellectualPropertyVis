#!/usr/bin/python3
    
from __future__  import print_function  # Python 2/3 compatibility

from gremlin_python import statics
from gremlin_python.structure.graph import Graph
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.strategies import *
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.traversal import T
import networkx as nx
import collections
import numpy as np
import re
from WordFile import WordFile, Entry
import itertools
from utils import add_to_dict
from operator import itemgetter
import sys
        
if __name__ == '__main__':

    import json

    collection = 'BT_43'
    year = sys.argv[1]
    #data = json.load(open("../Data/Labelled/" + collection + "_1872_field_labels.json", 'rb'))
    data = WordFile("../Data/Labelled/" + collection + "_address_labels.psv") #BT_43_1872_address_labels

    lastAddressSum = {}
    location_file = open("../Data/Extracted/BT_43_locations.psv","w")
    location_lookup = open("../Data/Extracted/BT_43_address_location_lookup.psv","w")
    address_lookup_dict = {}
    location_hash_lookup = {}
    hash_location_lookup = {}
    
    for entry in data:
        valid_items = [e for e in entry.items if e[1] not in ['w','ec','wc','sw','n','ne','se','e','-','nw','?']]
        entry_hash = entry.hash()
        i = len(valid_items)-1
        while i >=0 and valid_items[i][4] not in ['B-APT','I-APT']:
            i -= 1
        if i >= 0:
            this_item = valid_items[i][1]
            if this_item not in lastAddressSum:
                location_entry = Entry()
                location_entry.add_token('Location','B-FLD')
                location_entry.add_token(':', 'I-FLD')
                if valid_items[i][4] == 'I-APT':
                    location_entry.add_token(valid_items[i-1][1], 'B-APT')
                location_entry.add_token(this_item, valid_items[i][4])
                location_hash = location_entry.hash()
                location_entry.set_reference(location_hash)
                location_entry.write_to_file(location_file)
                location_hash_lookup[location_hash] = this_item
                hash_location_lookup[this_item] = location_hash
            add_to_dict(lastAddressSum, this_item)
            location_lookup.write(entry_hash + "|" + hash_location_lookup[this_item] + "|" + this_item + "\n")
            address_lookup_dict[entry_hash] = [hash_location_lookup[this_item], this_item]
        else:
            print("No address:",entry.get_tokens())
            #break
        
    location_file.close()
    location_lookup.close()
    
    sorted_sum = sorted([(k,v) for k,v in lastAddressSum.items()], key=itemgetter(1), reverse=True)
    
    #for s in sorted_sum:
    #    print(s)
    #print(sum([x[1] for x in sorted_sum]))

    #exit()
    
    c = 0
    
    buffer_len = 5
    buffer_list = []
    

    nept_graph = Graph()
    
    remoteConn = DriverRemoteConnection('wss://intellectual-property-instance-dev.c7ayd6bnaegk.eu-west-2.neptune.amazonaws.com:8182/gremlin','g')
    
    #strategyA = PartitionStrategy(partitionKey="_partition", writePartition="a", readPartitions=["a"])
    partitionA = PartitionStrategy(partition_key="partition_key",
                          write_partition="Main",
                          read_partitions=["Main"])
    
    partitionB = PartitionStrategy(partition_key="partition_key",
                          write_partition="AddressSum",
                          read_partitions=["AddressSum"])
    
    g = nept_graph.traversal().withRemote(remoteConn).withStrategies(partitionA)
    
    #g.V().hasLabel('location').drop().iterate()
    
    for h,l in location_hash_lookup.items():
        L = g.addV('location').property('id', h).property('name', l).next()

    
    subject_ids = {}
    
    data = WordFile("../Data/Extracted/BT_43_" + year + "_address_words.psv")
    
    reference_vertex_lookup = {}
    D = g.V().hasLabel('record').valueMap(True).toList(); 
    
    for d in D:
        reference_vertex_lookup[d['id'][0]] = d[T.id]
        
    location_vertex_lookup = {}
    D = g.V().hasLabel('location').valueMap(True).toList(); 
    
    for d in D:
        location_vertex_lookup[d['id'][0]] = d[T.id]
    
    print("Records:",data.length())
    for entry in data:
        entry_text = " ".join(entry.get_tokens())
        entry_hash = entry.hash()
        entry_ref = entry.get_reference()
        if entry_hash in address_lookup_dict:
            location_hash = address_lookup_dict[entry_hash][0]
            location = address_lookup_dict[entry_hash][1]
        else:
            print("No location match:",entry_ref,entry_text)
            continue
        
        #buffer_list.append([entry.metadata, " ".join(list(itertools.takewhile(lambda x: x != ".", )))])
        
        if entry_ref in reference_vertex_lookup:
            buffer_list.append([reference_vertex_lookup[entry_ref], location_vertex_lookup[location_hash]])
            if location != g.V(location_vertex_lookup[location_hash]).valueMap(True).toList()[0]['name'][0]:
                print(location, g.V(location_vertex_lookup[location_hash]).valueMap(True).toList()[0]['name'], entry_text)
        else:
            print(entry_ref, "not in lookup")
            continue

        c += 1
    
        if len(buffer_list) < buffer_len:
            continue

        
        #print(buffer_list)
        g.V(buffer_list[0][0]).addE('has_location').to(__.V(buffer_list[0][1])).property('weight', 1) \
         .V(buffer_list[1][0]).addE('has_location').to(__.V(buffer_list[1][1])).property('weight', 1) \
         .V(buffer_list[2][0]).addE('has_location').to(__.V(buffer_list[2][1])).property('weight', 1) \
         .V(buffer_list[3][0]).addE('has_location').to(__.V(buffer_list[3][1])).property('weight', 1) \
         .V(buffer_list[4][0]).addE('has_location').to(__.V(buffer_list[4][1])).property('weight', 1) \
         .iterate()
        
        buffer_list = []
        
        if c % 500 == 0:
            print("Created:", c)
    
    

    print("Graph nodes", len([v for v in g.V()]))
    print("Graph edges", len([e for e in g.E()]))
    
    remoteConn.close()

