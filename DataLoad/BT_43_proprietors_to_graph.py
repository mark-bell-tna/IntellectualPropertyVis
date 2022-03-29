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
from WordFile import WordFile
import sys

        
if __name__ == '__main__':

    import json

    collection = 'BT_43'
    year = sys.argv[1]
    drop = False
    #data = json.load(open("../Data/Labelled/" + collection + "_1872_field_labels.json", 'rb'))
    data = WordFile("../Data/Extracted/" + collection + "_" + year + "_unique_proprietors.psv")

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
    
    if drop:
        g.V().hasLabel('proprietor').drop().iterate()
    #exit()

    #g.addV('collection').property('id', collection).property('name', collection).next()
    #date_lookup = dict()
    
    file_refs = set()
    for entry in data:
        c += 1
        #print(g.V().has('proprietor','id',entry.get_reference()).valueMap(True).toList())
        this_ref = entry.get_reference()
        file_refs.add(this_ref)
        if len(g.V().has('proprietor','id',this_ref).toList()) == 0:
            buffer_list.append([this_ref, " ".join(entry.get_tokens())])
        else:
            continue
            #break
        
        if len(buffer_list) < buffer_len:
            continue
        
        V = g.addV('proprietor').property('id', buffer_list[0][0]).property('name', buffer_list[0][1]) \
         .addV('proprietor').property('id', buffer_list[1][0]).property('name', buffer_list[1][1]) \
         .addV('proprietor').property('id', buffer_list[2][0]).property('name', buffer_list[2][1]) \
         .addV('proprietor').property('id', buffer_list[3][0]).property('name', buffer_list[3][1]) \
         .addV('proprietor').property('id', buffer_list[4][0]).property('name', buffer_list[4][1]) \
         .iterate()
        
        buffer_list = []
        
        if c % 500 == 0:
            print("Processed:", c)
    print("Processed:",c)
    print(buffer_list)
    for b in buffer_list:
        g.addV('proprietor').property('id', b[0]).property('name', b[1]).next()
    

    data = WordFile("../Data/Extracted/" + collection + "_" + year + "_proprietor_words.psv")

    c = 0
    
    buffer_len = 5
    buffer_list = []
    
    
    reference_vertex_lookup = {}
    D = g.V().hasLabel('record').valueMap(True).toList(); 
    
    for d in D:
        reference_vertex_lookup[d['id'][0]] = d[T.id]
    
    proprietor_vertex_lookup = {}
    D = g.V().hasLabel('proprietor').valueMap(True).toList(); 
    
    for d in D:
        proprietor_vertex_lookup[d['id'][0]] = d[T.id]
    
    for entry in data:
        c += 1
        this_ref = entry.metadata['reference']
        
        this_hash = entry.hash()
        try:
            buffer_list.append([reference_vertex_lookup[this_ref], proprietor_vertex_lookup[this_hash]])
        except:
            print(this_ref, " ".join(entry.get_tokens()))
            continue
        
        if len(buffer_list) < buffer_len:
            continue
        
        g.V(buffer_list[0][0]).addE('has_proprietor').to(__.V(buffer_list[0][1])).property('weight', 1) \
         .V(buffer_list[1][0]).addE('has_proprietor').to(__.V(buffer_list[1][1])).property('weight', 1) \
         .V(buffer_list[2][0]).addE('has_proprietor').to(__.V(buffer_list[2][1])).property('weight', 1) \
         .V(buffer_list[3][0]).addE('has_proprietor').to(__.V(buffer_list[3][1])).property('weight', 1) \
         .V(buffer_list[4][0]).addE('has_proprietor').to(__.V(buffer_list[4][1])).property('weight', 1) \
         .iterate()
         
        buffer_list = []
        if c % 1000 == 0:
            print("Created:", c)
    
    for r in buffer_list:
        g.V(r[0]).addE('has_proprietor').to(__.V(r[1])).property('weight', 1).iterate()
        
    print("Graph nodes", len([v for v in g.V()]))
    print("Graph edges", len([e for e in g.E()]))
    
    remoteConn.close()

