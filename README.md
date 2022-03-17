# IntellectualPropertyVis
Web front end for Intellectual Property project

## Instructions

System is based on AWS infrastructure to host the data and web pages, and to query the database via an API

Before running installation scripts, edit the scripts/initialise_variables.bsh script to set project variables

Run scripts in the scripts directory in the following order to install AWS components
1. create_lambda.bsh
2. create_rest_api.bsh
3. create_s3_bucket.bsh
