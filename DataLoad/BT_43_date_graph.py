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


        
if __name__ == '__main__':

    import json

    collection = 'COPY_1'
    partition = "COPY_1"
    #data = json.load(open("../Data/Labelled/" + collection + "_1872_field_labels.json", 'rb'))
    data = WordFile("../Data/Source/" + collection + "_1862_words.psv")

    c = 0
    
    buffer_len = 5
    buffer_list = []
    

    nept_graph = Graph()
    
    remoteConn = DriverRemoteConnection('wss://intellectual-property-instance-dev.c7ayd6bnaegk.eu-west-2.neptune.amazonaws.com:8182/gremlin','g')
    
    #strategyA = PartitionStrategy(partitionKey="_partition", writePartition="a", readPartitions=["a"])
    partitionA = PartitionStrategy(partition_key="partition_key",
                          write_partition=partition,
                          read_partitions=[partition])
    
    partitionB = PartitionStrategy(partition_key="partition_key",
                          write_partition="AddressSum",
                          read_partitions=["AddressSum"])
    
    g = nept_graph.traversal().withRemote(remoteConn).withStrategies(partitionA)

    g.V().hasLabel('year').drop().iterate()
    
    print("Graph nodes", len([v for v in g.V()]))
    print("Graph edges", len([e for e in g.E()]))
    
    D = g.V().hasLabel('record_date').valueMap(True).toList();
    
    print("Dates to add", len(D))
    years = {}
    
    counter = 0
    for dt in D:
        year = dt['name'][0][0:4]
        dt_id = dt[T.id]
        if year not in years:
            Y = g.addV('year').property('id', year).property('name', year).next()
            years[year] = Y.id
            print("Added year:", year)
        year_node = years[year]
        g.V(dt_id).addE('is_year').to(__.V(year_node)).property('weight', 1).iterate()
        counter += 1
        if counter % 50 == 0:
            print("Added:",counter)

    print("Graph nodes", len([v for v in g.V()]))
    print("Graph edges", len([e for e in g.E()]))
    remoteConn.close()


    