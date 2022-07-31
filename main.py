import logging

from aiohttp import web

from app.context import AppContext
from app import routes


def create_app() -> web.Application:
    app = web.Application()

    context = AppContext()

    app.on_startup.append(context.on_startup)
    app.on_shutdown.append(context.on_shutdown)

    routes.setup_routes(app, context)

    return app


def main():
    logging.basicConfig(level=logging.DEBUG)
    app = create_app()
    web.run_app(app)


if __name__ == "__main__":
    main()
