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
import itertools


        
if __name__ == '__main__':

    import json

    collection = 'BT_43'
    #data = json.load(open("../Data/Labelled/" + collection + "_1872_field_labels.json", 'rb'))
    data = WordFile("../Data/Extracted/" + collection + "_1872_subject_words.psv")

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
    
    g.V().hasLabel('subject').drop().iterate()
    
    subject_ids = {}
    
    reference_vertex_lookup = {}
    D = g.V().hasLabel('record').valueMap(True).toList(); 
    
    for d in D:
        reference_vertex_lookup[d['id'][0]] = d[T.id]
        
    subject_reference_lookup = {}
    
    for entry in data:
        c += 1
        entry_text = " ".join(entry.get_tokens())
        entry_hash = entry.hash()
        if entry_text not in subject_ids:
            V = g.addV('subject').property('id', entry_hash).property('name', entry_text).next()
            subject_ids[entry_text] = V.id
        
        #buffer_list.append([entry.metadata, " ".join(list(itertools.takewhile(lambda x: x != ".", )))])
        buffer_list.append([reference_vertex_lookup[entry.get_reference()], subject_ids[entry_text]])
    
        if len(buffer_list) < buffer_len:
            continue
        
        g.V(buffer_list[0][0]).addE('has_subject').to(__.V(buffer_list[0][1])).property('weight', 1) \
         .V(buffer_list[1][0]).addE('has_subject').to(__.V(buffer_list[1][1])).property('weight', 1) \
         .V(buffer_list[2][0]).addE('has_subject').to(__.V(buffer_list[2][1])).property('weight', 1) \
         .V(buffer_list[3][0]).addE('has_subject').to(__.V(buffer_list[3][1])).property('weight', 1) \
         .V(buffer_list[4][0]).addE('has_subject').to(__.V(buffer_list[4][1])).property('weight', 1) \
         .iterate()
        
        buffer_list = []
        
        if c % 500 == 0:
            print("Created:", c)
    
    for b in buffer_list:
        g.V(b[0]).addE('has_subject').to(__.V(b[1])).property('weight', 1).next()

    print("Graph nodes", len([v for v in g.V()]))
    print("Graph edges", len([e for e in g.E()]))
    
    remoteConn.close()

