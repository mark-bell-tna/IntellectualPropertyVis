#!/usr/bin/python3
    
from __future__  import print_function  # Python 2/3 compatibility

from gremlin_python import statics
from gremlin_python.structure.graph import Graph
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.strategies import *
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.traversal import T
import collections
import re
from WordFile import WordFile
import sys

        
if __name__ == '__main__':

    import json

    collection = 'BT_43'
    year = sys.argv[1]
    #data = json.load(open("../Data/Labelled/" + collection + "_1872_field_labels.json", 'rb'))
    data = WordFile("../Data/Source/" + collection + "_" + year + "_words.psv")

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
    
    
    print("Graph nodes", len([v for v in g.V()]))
    print("Graph edges", len([e for e in g.E()]))
    
    g.addV('collection').property('id', collection).property('name', collection).next()
    collection_id = g.V().has('collection', 'id', collection).valueMap(True).toList()[0][T.id];
    date_lookup = dict()
    
    for entry in data:
        c += 1
        buffer_list.append(entry.metadata)
        this_date = entry.metadata['from_date']
        if this_date not in date_lookup:
            V = g.addV('record_date').property('name', this_date).next()
            date_lookup[this_date] = V.id
            
        if len(buffer_list) < buffer_len:
            continue
        
        g.addV('record').property('id', buffer_list[0]['reference']).property('name', buffer_list[0]['reference']) \
        .addV('record').property('id', buffer_list[1]['reference']).property('name', buffer_list[1]['reference']) \
        .addV('record').property('id', buffer_list[2]['reference']).property('name', buffer_list[2]['reference']) \
        .addV('record').property('id', buffer_list[3]['reference']).property('name', buffer_list[3]['reference']) \
        .addV('record').property('id', buffer_list[4]['reference']).property('name', buffer_list[4]['reference']) \
        .iterate()
         
        buffer_list = []
        
        if c % 500 == 0:
            print("Created:", c)
            
    for r in buffer_list:
        
        g.addV('record').property('id', r['reference']).property('name', r['reference']).iterate()
    
    buffer_list = []
    print("Graph nodes", len([v for v in g.V()]))
    print("Graph edges", len([e for e in g.E()]))
    
    reference_vertex_lookup = {}
    D = g.V().hasLabel('record').valueMap(True).toList(); 
    
    for d in D:
        reference_vertex_lookup[d['id'][0]] = d[T.id]
    
    date_vertex_lookup = {}
    D = g.V().hasLabel('record_date').valueMap(True).toList(); 
    
    for d in D:
        date_vertex_lookup[d['name'][0]] = d[T.id]
        
    for entry in data:
        c += 1
        buffer_list.append([reference_vertex_lookup[entry.get_reference()], date_vertex_lookup[entry.metadata['from_date']]])
            
        if len(buffer_list) < buffer_len:
            continue
        
        #print(buffer_list)
        g.V(collection_id).addE('has_record').to(__.V(buffer_list[0][0])).property('weight', 1) \
         .V(collection_id).addE('has_record').to(__.V(buffer_list[1][0])).property('weight', 1) \
         .V(collection_id).addE('has_record').to(__.V(buffer_list[2][0])).property('weight', 1) \
         .V(collection_id).addE('has_record').to(__.V(buffer_list[3][0])).property('weight', 1) \
         .V(collection_id).addE('has_record').to(__.V(buffer_list[4][0])).property('weight', 1) \
         .iterate()
        
        g.V(buffer_list[0][0]).addE('has_date').to(__.V(buffer_list[0][1])).property('weight', 1) \
         .V(buffer_list[1][0]).addE('has_date').to(__.V(buffer_list[1][1])).property('weight', 1) \
         .V(buffer_list[2][0]).addE('has_date').to(__.V(buffer_list[2][1])).property('weight', 1) \
         .V(buffer_list[3][0]).addE('has_date').to(__.V(buffer_list[3][1])).property('weight', 1) \
         .V(buffer_list[4][0]).addE('has_date').to(__.V(buffer_list[4][1])).property('weight', 1) \
         .iterate()
         
        buffer_list = []
        
        if c % 500 == 0:
            print("Created:", c)
    
    for r in buffer_list:
        
        g.V(collection_id).addE('has_record').to(__.V(r[0])).property('weight', 1).iterate()
        
        g.V(r[0]).addE('has_date').to(__.V(r[1])).property('weight', 1).iterate()
    
    print("Graph nodes", len([v for v in g.V()]))
    print("Graph edges", len([e for e in g.E()]))
    
    
    remoteConn.close()

