# OpenWeather API

The API was built with Python 3 using the AIOHTTP Asynchronous HTTP Client / Server for asyncio framework.

This service collects data from an Open Weather API and stores it as JSON data in a sqlite database.

The free account of the OpenWeather API has a limit of 60 calls/minute so this API respects this limit.


## Installation

Run **docker-compose up** to *start* the application.

Run **docker-compose down** *stops* containers and removes containers, networks, volumes, and images created by up.

Run **docker-compose build** or **docker-compose up --build** to rebuild.


## Usage

The local API service must be available after the command * docker-compose up * on port 7007.

The **POST** endpoint:
```html
/weather/unit of measurement/api key/list of city IDs
```
[Units of measurement](https://openweathermap.org/current#data)
[API Key](https://home.openweathermap.org/users/sign_up)
[City ID](https://openweathermap.org/current#cityid)

The **GET** endpoint:
```html
/weather/requestID
```

Create an account at [OpenWeather](https://openweathermap.org/) API to generate a token to call their API.

In the **test** folder, there are two *post_weather_city_id.py* and *get_weather_progress.py* scripts available to test the API.

The **post_weather_city_id.py** is an async script responsible for calling the OpenWeather API passing as parameters the api Key and a list of city ID.

Example:
```python
url = 'http://localhost:7007'
api_key = 'your api key here'
city_id_list = [3439525, 3439781, 3440645]

```

The request will return a unique ID, save it to see the progress of the request.

Example:
```json
{"RequestID": "132e6d67-0424-49fe-88ad-c208d9d2ee62"}
```



The **get_weather_progress.py** is an async script returns with the percentage of the POST progress ID (collected cities completed) until the current moment..

Example:
```python
url = 'http://localhost:7007'
request_ids = ['4615c7a3-2b4f-452f-bcb5-acb00765ca22','4615c7a3-2b4f-452f-bcb5-acb00765ca22']
```
The ID request will return the progress of the POST request or a message if it encounters any problems.

Example:
```json
{"requestID": "132e6d67-0424-49fe-88ad-c208d9d2ee62", "progress": "77.8%"}
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
