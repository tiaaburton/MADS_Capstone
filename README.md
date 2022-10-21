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

Congrats, Market Shopper! The app is now running in the container, and you can access the app by heading to the
heading to your default browse and enter:
~~~
https://localhost:5000/
~~~

### Loading the Datasets
...

### Login to the App
...
