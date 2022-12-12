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
1. Google - API keys for the Google login interface. Instructions to obtain an API key can be found [here](https://developers.google.com/identity/oauth2/web/guides/get-google-api-clientid).
2. Fred - Retrieve the latest federal data.
3. Expert AI - Classify social media text as good or bad.
4. Twitter - API for accessing Twitter data for particular stocks
5. Redit - API for accessing Redit data for particular stocks

To add the new config.ini file, that is presumably within your Downloads folder. Run the two commands below and rerun the Docker container from Docker Desktop.

~~~
cd Downloads/
docker cp config.ini basket:/opt/app/src/config.ini
~~~


If you fork the GitHub or iterate on the Docker image, you may add or remove functionality with the APIs listed above.

#### On Success:

Congrats, Market Shopper! The app is now running in the container, and you can access the app by heading to the
heading to your default browse and enter:
~~~
https://localhost:5000/
~~~
Note: The local host for your machine may be different. For testing purposes, the local host used was 
```http://127.0.0.1:5000/``` for a Mac with iOS.

### Loading the Datasets
To load the datasets, you will first need to setup a MongoDB database.  For this project, we used MongoDB Atlas, however, for personal use, we would 
recommend [MongoDB Community edition](https://www.mongodb.com/try/download/community) instead.  

Once you have [created a user/password](https://www.mongodb.com/docs/manual/tutorial/create-users/) with read, update, and delete permissions in MongoDB, please follow the below steps:

1. Create a new database called "market_shopper"
2. Insert your credentials into the config.ini file
3. Within the codebase, run the following methods:
    * src/data/fred/initialize_fred()
    * src/data/sec/initialize_sec()
    * src/data/yahoo/initialize_yahoo()
4. The data should now be flowing into MongoDB.  These methods will take some time to load the data (6+ hours).  Once loaded however, you can simply run update_daily.py each day to update the data.

While you may have loaded the data locally, the data is owned by [FRED](https://fred.stlouisfed.org/), the [SEC](https://www.sec.gov/), and [Yahoo Finance](https://finance.yahoo.com/) and is intended only for personal use.

### Login to the App
Note that this app is available to all with an active Gmail account. Because the application is in development, there isn't an external link. It must be ran locally with docker or CLI. However, the login is for added security
with items stored in the session.

If you receive an error while login in, please return to the previous URL and click the dashboard button. This will allow you immediate access.

### Purpose per Page
* **Home** - Review the market and find new metrics.
* **Portfolio** - Analyze your portfolio after uploading a csv like the test_portfolio.  Example shown below for column naming.
* **Analysis** - Analyzes specific signals for a particular stock include its sentiment on Twitter and Reddit, its weighted moving average, and its KDJ indicator.
* **Discovery** - Allows for the discovery of new stocks to invest in by showing the previous growth rate, expected growth rate fron analysts, and predicted growth rate from a machine learning model
* **Prediction** - Predicts the overall market trends over the next few months and compares the market with previous trends.

### Portfolio Naming
If you would like to add a portfolio to the tool, you must upload a comma separated value file with the following naming convention:

| **Symbol** | **Price** | **Cost** | **Share** |
|------------|-----------|----------|-----------|
| MCD        | 273.9     | 239.63   | 20        |
| BABA       | 86.33     | 107.09   | 15        |
