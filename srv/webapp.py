import logging.config
import tornado.ioloop
import tornado.web
import tornadoredis

import handlers
import conf


def make_app(redis_conn):
    return tornado.web.Application([
        (r'/signup', handlers.SignUpHandler, dict(redis_conn=redis_conn)),
        (r'/signin', handlers.SignInHandler, dict(redis_conn=redis_conn)),
        (r'/chat/(.*)', handlers.ChatHandler),
    ] + [
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": conf.STATIC_DIR}),
    ] if conf.SERVE_STATIC else [])

if __name__ == "__main__":
    logging.config.dictConfig(conf.WEBAPP_LOG_CONFIG)

    c = tornadoredis.Client(host=conf.REDIS_HOST)
    c.connect()

    app = make_app(c)
    app.listen(conf.PORT)
    logging.info('Starting on port %d' % conf.PORT)
    tornado.ioloop.IOLoop.current().start()
