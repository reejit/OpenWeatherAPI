# coding=utf-8
from aiohttp import web, ClientSession
import aiohttp_cors
from pony.orm import Database, PrimaryKey, Required, Set, db_session, delete, Optional, Json, select
from pony.orm.core import TransactionIntegrityError, CacheIndexError, ConstraintError
import jinja2
import aiohttp_jinja2
from time import strftime, localtime
from os import path, environ
from asyncio import Queue, ensure_future, sleep
from uuid import uuid4


ROOT_DIR = path.dirname(path.abspath(__file__))
db = Database()

# date template
DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# orm class
# -------------------------------------------------------------------------------------------------
class Weather(db.Entity):
    wthr_id = PrimaryKey(int, auto=True)
    wthr_request_id = Required(str, index='idx_wthr_req_id')
    whtr_datetime = Required(str, default=lambda: strftime(DATE_TIME_FORMAT, localtime()))
    wthr_data = Required(Json)

# -------------------------------------------------------------------------------------------------
async def index(request):
    """
    I serve a page to check the status of the server
    """
    return aiohttp_jinja2.render_template('index.html', request, context={'app': 'Open Weather API'})


# -------------------------------------------------------------------------------------------------
# noinspection PyUnusedLocal
@db.on_connect(provider='sqlite')
def sqlite_case_sensitivity(database, connection):
    cursor = connection.cursor()
    # auto_vacuum is an optional feature that automatically
    # vacuums the database to minimize the size of the database file
    cursor.execute('PRAGMA auto_vacuum = FULL')
    cursor.execute('vacuum')


# -------------------------------------------------------------------------------------------------
async def get_weather(request):
    """
    I get the data from openweather
    :param request: api key and a list of city Ids
    :return: a unique request id
    """
    # i get the user's api key
    request_id = request.match_info['requestID']
    # i get information about the progress of requests
    progress = REQUEST_STATUS.get(request_id)
    if progress is not None:
        return web.json_response({'requestID': request_id,
                                  'progress': "{}%".format(progress)})

    with db_session:
        # I get the number of requests processed
        req_id_count = select(c for c in Weather
                              if c.wthr_request_id == '{rid}'.format(rid=request_id)).count()

    return web.Response(text='No progress information was found for that ID {} '
                             'but {} request/s were found for that ID.'.format(request_id, req_id_count))


# -------------------------------------------------------------------------------------------------
async def post_weather(request):
    """
    I get the data from openweather
    :param request: api key and a list of city Ids
    :return: a unique request id
    """
    try:
        # i get the unit of measurement
        unit_measurement = request.match_info['unitMeasurement']
        # i get the user's api key
        api_key = request.match_info['apiKey']
        # i get the list of city IDs
        city_list = request.match_info['cityList']
        # i get the list of city ids
        city_id_list = eval(city_list)
        # check if it's a list
        if isinstance(city_id_list, list) and len(city_id_list):
            # i get a unique request id
            request_id = str(uuid4())
            # i save the request ID to track the status of the request
            REQUEST_STATUS.update({request_id: 0, 'items': len(city_id_list)})
            # get city IDS
            for city_id in city_id_list:
                # add information to a queue to start processing and controlling requests per minute
                await queue.put((unit_measurement, api_key, len(city_id_list), request_id, city_id))
            # return a unique ID that identifies the processing of this request
            return web.json_response({'RequestID': '{}'.format(request_id)})
        else:
            # processing could not be continued
            return web.Response(text='The request could not be processed.')
    except BaseException as e_post_weather:
        return web.Response(text="Error: {}".format(e_post_weather))


# -------------------------------------------------------------------------------------------------
async def consumer(q):
    while True:
        minute = localtime().tm_min
        count = 0
        while not q.empty():
            min = localtime().tm_min
            # 60 is the maximum number of requests per second
            if count < 60 and minute == min:
                unit_measurement, api_key, total_ids, request_id, city_id = await q.get()
                async with ClientSession() as session:
                    try:
                        async with session.get('http://api.openweathermap.org/data/2.5/weather?'
                                               'units={unitMeasurement}&'
                                               'id={city_id}&'
                                               'appid={api_key}'.format(unitMeasurement=unit_measurement,
                                                                        city_id=city_id,
                                                                        api_key=api_key)
                                               ) as resp:
                                    response = await resp.json()
                                    if resp.status == 200:
                                        # get the main data from response
                                        open_weather_main = response.get('main')
                                        # get the temp
                                        temp = open_weather_main.get('temp')
                                        # get the humidity
                                        humidity = open_weather_main.get('humidity')

                                        with db_session:
                                            Weather(wthr_request_id=request_id,
                                                    wthr_data={'cityID': city_id,
                                                              'temperature': temp,
                                                              'humiduty': humidity})


                                            req_id_count = select(c for c in Weather
                                                                  if c.wthr_request_id == '{rid}'.format(rid=request_id)).count()
                                            # i calculate the progress
                                            progress = round((req_id_count*100)/total_ids, 1)
                                            # i keep the data in a dict
                                            REQUEST_STATUS.update({request_id: progress})
                                    else:
                                        REQUEST_STATUS.update({request_id: "{}".format(response)})

                    except BaseException as e_open_weather:
                        print('e_open_weather: {}'.format(e_open_weather))
                q.task_done()
                count += 1
                await sleep(0.1)
            elif minute != min:
                minute = min
                count = 0
            elif minute != min and count >= 60:
                count = 0

            await sleep(0.1)

        await sleep(1)


# -------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    try:
        REQUEST_STATUS = {}
        queue = Queue(maxsize=5000)
        # It is used for attaching declared entities to a specific database
        db.bind(provider='sqlite', filename=path.join(ROOT_DIR,'app.sqlite'), create_db=True)
        # db.bind(provider='sqlite', filename=':memory:')
        # The parameter create_tables=True indicates that, if the tables do not already exist,authUser
        # then they will be created using the CREATE TABLE command.
        db.generate_mapping(create_tables=True)
        # ==============================================================================================
        ensure_future(consumer(queue))
        # ==============================================================================================
        # start web server settings
        app = web.Application(client_max_size=2048 ** 2)
        # I configure the engine to render the templates
        aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('{}/dist'.format(ROOT_DIR)))
        # Cross-origin resource sharing
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers='*',
                allow_headers='*'
            ),
        })
        # inform the API REST routes that will be used in the application
        routes = [
            {'method': 'GET', 'path': '/', 'handler': index},
            {'method': 'GET', 'path': r'/weather/{requestID:.*}', 'handler': get_weather},
            {'method': 'POST', 'path': r'/weather/{unitMeasurement:.*}/{apiKey:.*}/{cityList:.*}', 'handler': post_weather},
        ]

        # apply cors on routes
        for route in routes:
            cors.add(
                app.router.add_route(
                    method=route['method'],
                    path=route['path'],
                    handler=route['handler']
                )
            )

        # I connect the web server using port 7007
        web.run_app(app=app, port=int(environ.get('PORT', 7007)))

    except BaseException as e_app:
        print('e_app: {}'.format(e_app))
