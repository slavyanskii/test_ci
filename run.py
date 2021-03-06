import argparse, asyncio

from aiohttp import web

from app.db_client import DBAsyncClient
from app.router import setup_routes
from run_migrations import run_migrations


async def db_middleware(app, handler):
    async def middleware(request):
        request['db'] = app['db']
        return await handler(request)

    return middleware


async def error_middleware(app, handler):
    async def middleware_error_handler(request):
        try:
            response = await handler(request)
            if response.status == 404:
                return web.FileResponse('static/not_found.html')
            return response
        except web.HTTPException as ex:
            if ex.status == 404:
                return web.FileResponse('static/not_found.html')
            raise
    return middleware_error_handler


def start_app(port):
    app = web.Application(middlewares=[db_middleware, error_middleware])

    app['db'] = DBAsyncClient()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.ensure_future(run_migrations()))
    setup_routes(app)
    web.run_app(app, port=port)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', help='Port, on which server will be serving')
    args = parser.parse_args()
    port = int(args.port) if args.port else 5000
    start_app(port)
