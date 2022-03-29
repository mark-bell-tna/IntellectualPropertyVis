# IntellectualPropertyVis
Web front end for Intellectual Property project. There are four interactive visualisations embedded in HTML. Three are developed in D3 and one is vis.js (originally sourced from an Amazon tutorial [example](https://github.com/aws-samples/amazon-neptune-samples/tree/master/gremlin/visjs-neptune)).

The four visualisations are:
1. visualize-dates.html: Summary of records by day, filterable by Year and available for both BT/43 and COPY/1. Interactive components include: providing a day summary by company on click of a bar; Overlaying proprietor activity on mouse over proprietor.
2. visualize-by-place.html: Stacked chart of records by location (county, country, large city/town), and by Registered Design Class (BT/43 only). Filterable by year. Interactive components include: Numerical summary on click of location bar
3. visualize-graph.html: Browsable network visualisation of locations in BT/43 (1872). Uses vis.js as based on AWS example. Interactive components include: search for location; click to find sub-locations of node (e.g places in Yorkshire); ctrl+click to find parent of node (e.g. Yorkshire is parent of Leeds); alt+click to remove nodes form graph
4. visualize-words.html: Top 250 words (minus stop words) found in COPY/1 descriptions, size by frequency. Interactive components include: display barchart of co-located words on click of individual word

## Instructions

System is based on AWS infrastructure to host the data and web pages, and to query the database via an API

Before running installation scripts, edit the scripts/initialise_variables.bsh script to set project variables. Currently it is assumed that a Neptune database, a VPC and security groups are already in place.

Run scripts in the scripts directory in the following order to install AWS components
1. create_lambda.bsh
2. create_rest_api.bsh
3. create_s3_bucket.bsh - the name of the Bucket is set in the script and replaces the value of BUCKET_NAME below

The HTML files in this repository should then be uploaded to the S3 Bucket. The following command can be used to do this (replace HTML_FILE_NAME and BUCKET_NAME accordingly):
aws s3 cp HTML_FILE_NAME s3://BUCKET_NAME/HTML_FILE_NAME --acl public-read

Once uploaded an HTML file can be viewed at the following URL in a browser (again change values):
https://BUCKET_NAME.s3.eu-west-2.amazonaws.com/HTML_FILE_NAME
