# LeagueMatchPredictor

This project is a website that uses a machine learning model to predict which team in an active match of League of Legends will win and with that probability. 

I utilized the Riot Games API to collect the data of around 11,000 matches. Any other supplemental data was scraped from online League of Legends analytical sites using web scraping with the Beautiful Soup library from Python.

For predictions, I used the Riot Games Live Client Data API to gather information about an active match. I parsed this data and added web scraping for extra features before entering it into the random forest machine learning model.

In order too use this website, make sure you are in an active match of league of legends on the Summoner’s Rift map. You can check this by going to “https://127.0.0.1:2999/liveclientdata/allgamedata” and seeing if you get a response.

If you get a response, copy the data and go to liveleaguematchpredictor.herokuapp.com where there will be an text box for you to paste the copied data. Simply click the input button and you will enter a page similar to the images below.







































