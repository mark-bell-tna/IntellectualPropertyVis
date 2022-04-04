# Intellectual Property Visualisations project

This project has developed four visualisations for exploration of catalogue entries in The National Archives' collections related to Intellectual Property, in particular BT/43 (Registered Designs) and COPY/1 (Copyright). Each visualisation shows a different aspect of the records and includes interactive components to enable exploration. The first three visualisations use D3.js, and the fourth uses vis.js.

Each visualisation requests data from an Amazon Neptune database by calling a lambda function through an API Gateway. The lambda functions in turn use Gremlin to query the database. The data is separated into partitions: a Main partition for BT/43, a COPY_1 partition for COPY/1 data, and an AddressSum partition for the address data used by Visualisation 4.

## Visualisation 1: Summary by date

https://YOUR-S3-BUCKET-NAME.s3.eu-west-2.amazonaws.com/visualize-dates.html
    
[![Visualise Dates](Images/visualise-dates.png?raw=True)](https://github.com/mark-bell-tna/IntellectualPropertyVis/blob/main/Images/visualise-dates.png)

This is a bar chart showing counts of records by day (based on their start date in the catalogue). The URL includes a parameter for filtering by individual years (e.g. add ?year=1872 to the URL) or all of data can be displayed in one. Hyperlinks which use this filer are included in the HTML page to navigate to annual charts.
    
The source data for the graph comes from the following Gremlin query called through the API function getDateSummary:
    
```
  // P_V is a partition variable set at the beginning of the module
  var V;
  // This handles the year filtering
  if (year) {
     V = P_V.has('year', 'name', year).inE('is_year').outV().hasLabel('record_date')
  } else {
     V = P_V.hasLabel('record_date')
  }

  // Summarise the selected records by date and edge weight (always 1 but not necessarily the case for other kinds of catalogue records)
  data = await V
           .project('date','both')
             .by('name')
             .by(__.inE('has_date').values('weight').sum())
     .toList();
```
    
The chart includes the following interactive functionality:
    
    1. Hovering the mouse over a bar brings up a tooltip to display the date and count, as chart axes are not granular enough for this purpose. The source data is taken directly from the source of the graph.

    2. Clicking on a bar prints a summary below the chart of all proprietors who registered their designs on that day. An example summary from 17th August 1863 looks like this: Count: 20 -> proprietor : james black and company . -> scotland -> class 10 : printed fabrics
    The clicking event calls a Gremlin query through the API function proprietorsDateSummary:
    
    
```
data = await P_V
    .has('record_date','name', name)
    .as('date').inE().outV().as('reference')
    .project('date','proprietor', 'subject', 'class', 'location')
      .by(__.select('date').values('name'))
      .by(__.coalesce(__.select('reference').outE('has_proprietor').inV().values('name'), __.constant('unknown')))
      .by(__.coalesce(__.select('reference').outE('has_subject').inV().values('name'), __.constant('unknown')))
      .by(__.coalesce(__.select('reference').outE('has_class').inV().values('name'), __.constant('unknown')))
      .by(__.coalesce(__.select('reference').outE('has_location').inV().values('name'), __.constant('unknown')))
    .groupCount()
    .toList()
```

    The coalesce functions are required because the data isn't quite complete. For performance it may be better to include 'unknown' values in the database and remove the coalesce step.
    
    3. To the left of the proprietor information is a circle. Hovering over this circle overlays a summary of that proprietors registrations over the whole period of the graph onto the main graph. This enables quick identification of how frequently a proprietor registers their designs. The hover event calls the API function summarisingPropDates:
    
```
data = await g.V().has('partition_key', 'Main')
                .has('proprietor','name', name)
                .as('proprietor').inE('has_proprietor').outV().as('reference')
                .outE('has_date')
                .inV().as('date').values('name')
                .groupCount()
                .toList()
```
    
## Visualisation 2: Summary by location and class
    
    https://<S3 Bucket Name>.s3.eu-west-2.amazonaws.com/visualize-by-place.html
    
    [![Visualise Places](Images/visualise-by-place.png?raw=True)](Images/visualise-by-place.png)
    
    This is a horizontally stacked bar chart of registrations by location (last element of the address) with each bar further broken down by design class (e.g. textiles, metal). It has the same year filtering system as the date graph.
    
    The chart includes the following interactive feature:
    
    1. Clicking a bar opens up a table of counts by Class in a pop up by called the API function SummarisingLocations.
    
```
var V;
if (year) {
 V = P_V.has('year', 'name', year).inE('is_year').outV().inE('has_date').outV()
} else {
 V = P_V.hasLabel('record')
}

data = await V.as('record')
.outE('has_location').inV().as('location')
.project("loc","cls")
    .by(__.select('location').values('name'))
    .by(__.select('record').outE('has_class').inV().values('name'))
.groupCount()
.toList()
```    

## Visualisation 3: Copyright word colocations

    https://<S3 Bucket Name>.s3.eu-west-2.amazonaws.com/visualize-words.html
    
    This visualisation shows the top 250 words appearing in COPY/1 descriptions. They are positioned in alphabetical order and sized by number of appearances (on a logarithmic scale). The words are sourced through the API function TopCopy1Words
    
```
data = await P_V.hasLabel('top_word').valueMap().toList();
```
    
    The visualisation includes the following interactive functionality:
    
    1. Hovering over a word shows a bar chart above the word list which summarises the top 10 colacted (within a 2 word window) with the word in descriptions. The data is sourced through the API function WordColocations
    
```
data = await P_V.hasLabel('top_word').has('word',name).outE('has_colocation').as('edge').inV().as('co_word')
                .project("co_word","weight")
                  .by(__.select('co_word').values('word'))
                  .by(__.select('edge').values('weight'))
                .toList()
```
    
## Visualisation 4: Address summary graph
    
The address summary graph uses the vis.js library and is based on an Amazon sample from their Github repository. The source data is derived from addresses from 1872 in the BT/43 collection. Each address was separated by the comma delimiter and instances of each adjacent address part were counted (e.g. Manchester-Lancashire). The result was a network graph where each vertex was a part of an address (e.g. Manchester) and the adjacency counts stored on edges.
    
The user experience begins with a search for a location in a input box, the box incorporating autocomplete. Pressing the search button puts the location name as a node on the graph. Clicking this node finds all successor nodes - a successor node being places which appear before the selected node in addresses.
    
Example interaction:
    
    1. User searches for Leeds
    2. User clicks on Leeds node
    3. Nodes such as "boar lane" are added to the graph with a directed edge into them to the Leeds node. This means that at least one address contained "boar lane, leeds". In this case the edge was 1, so this did occur once.
    
If the user presses (no need to hold it) the Ctrl key before clicking on a node predecessor nodes will be retrieved instead. A predecessor is a location that occurs after the location that is clicked on, and can also be thought of as a parent or container.
    
Example interaction:
    
    1. User presses Ctrl, then clicks on Leeds
    2. The Yorkshire node is added to the graph with a directed edge to the Leeds node. In this case the edge weight is 13, which means the string "Leeds, Yorkshire" appears 13 times in the data.
    
Sometimes added nodes are called "^" or "$". These represent the beginning of an address or the end respectively and are used to separated cases where a node has or doesn't have successors or predecessors.
    
Example interaction:
    
    1. User clicks on the Leeds node
    2. The "^" node is added to the graph with a directed edge with weight of 2 from Leeds to "^". This means that two addresses were listed only as "Leeds, Yorkshire" with no town, street or building.
