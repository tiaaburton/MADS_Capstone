![Market Shopper](src/static/images/logo.png)

Market Shopper is an educational product designed to help democratize portfolio management by increasing access to institutional-like 
tools and analyses.

#### Status: Developmental
This app is in a development phase. When finished, the end user is a student interested in data science, an individual who would be
considered a beginner investor, or a person who would be interested in advancing or incorporating open source portfolio management
tools into their financial toolkit.

### Team

Tia Burton, Joshua Raymond, Joshua Nacey

### How to run the docker image?
First, ensure Docker Desktop is open. We recommend logging into Docker Desktop with your Docker Hub credentials.
This will allow for quick access through the command line interface (CLI). Start by downloading the docker image
from Docker Hub with the following command:

~~~
docker pull tiaaburton/market-shopper:latest
~~~

Next, invoke a new Docker Container, named basket, that will run the server locally with the necessary requirements
and environment variables set.
~~~
docker run --name=basket -p 5000:5000 -t tiaaburton/market-shopper:latest
~~~

Once the image is downloaded locally, locate the ```config_template.ini```. Create a copy within the src directory
named ```config.ini```. If this file does not exist, the app will not run. To use the app, you must create credentials
for the following:
1. Google - Credentials
2. Plaid - Securely connect to your portfolio
3. Fred - Retrieve the latest federal data
4. 

Congrats, Market Shopper! The app is now running in the container, and you can access the app by heading to the
heading to your default browse and enter:
~~~
https://localhost:5000/
~~~
Note: The local host for your machine may be different. For testing purposes, the local host used was 
http://127.0.0.1:5000/

### Loading the Datasets
...

### Login to the App
Note that this app is available to all with an active Gmail account. Because the application is in development,
there isn't an external link. It must be ran locally with docker or CLI. However, the login is for added security
with items stored in the session.

### Purpose per Page
* Home
* Portfolio - Log into your retirement and investment accounts securely to view portfolio management measures 
and techniques.
* Analysis
* Discovery
* Prediction

### Glossary
* Safety First Measures
* KDJ Indicator
* 
