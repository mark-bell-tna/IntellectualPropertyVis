# IntellectualPropertyVis
Web front end for Intellectual Property project

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
