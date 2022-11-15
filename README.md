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

Don't be alarmed; the container will run momentarily, but it will end with an **Exited** status. We need to add a file into the container. 
Once the image is downloaded locally and the container exists, locate the ```config_template.ini``` file in [GitHub](https://github.com/tiaaburton/MADS_Capstone/blob/main/src/config_template.ini). 
Download the file and make a copy named ```config.ini```. The app will not run because this file does'nt exist. To use the app,
you must create credentials for the following:
1. Google - Credentials to log in with Google.
2. Plaid - Securely connect to your portfolio information or test information.
3. Fred - Retrieve the latest federal data.
4. Expert AI - Classify social media text as good or bad.

To add the new config.ini file, that is presumably within your Downloads folder. Run the two commands below
and rerun the Docker container from Docker Desktop.

~~~
cd Downloads/
docker cp config.ini basket:/opt/app/src/config.ini
~~~


If you fork the GitHub or iterate on the Docker image, you may add or remove functionality with
the APIs listed above.

#### On Success:

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
