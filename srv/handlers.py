import json
import logging

import tornado.gen
import tornado.web
import tornado.websocket

import auth


class JSONHandler(tornado.web.RequestHandler):
    MIME_TYPE = 'application/json'

    @property
    def json_request(self):
        if (
            self.request.headers.get(
                'Content-type', ''
            ).startswith(self.MIME_TYPE)
        ):
            if self.request.body:
                try:
                    parsed = json.loads(self.request.body.decode('latin1'))
                except ValueError as e:
                    raise tornado.web.HTTPError(400, 'Malformed JSON')
            else:
                raise tornado.web.HTTPError(400, 'Empty body')
        else:
            parsed = None

        return parsed

    def reply(self, data, status_code=200):
        result = json.dumps(data, ensure_ascii=True)
        self.set_header('Content-type', 'application/json; charset=latin1')
        self.set_status(status_code)

        self.finish(result)

    def write_error(self, status_code, **kwargs):
        cls, error = kwargs.get('exc_info', (None,) * 2)[0:2]

        if cls is tornado.web.HTTPError:
            logging.error(error)
            self.reply(
                {
                    'status': 'error',
                    'reason': error.log_message
                },
                status_code
            )
        else:
            super(JSONHandler, self).write_error(status_code, **kwargs)


class RedisAwareHandler(tornado.web.RequestHandler):
    def initialize(self, redis_conn=None):
        if redis_conn is None:
            raise RuntimeError('No connection to redis provided')

        self.redis_conn = redis_conn


def extract_credentials(req):
    try:
        return req['username'], req['password']
    except KeyError:
        raise tornado.web.HTTPError(
            400, 'Username and password are reqired for signup.'
        )


class SignUpHandler(JSONHandler, RedisAwareHandler):
    def initialize(self, redis_conn):
        super(SignUpHandler, self).initialize(redis_conn)

        self.signup_lock = redis_conn.lock("signup_lock", lock_ttl=10, polling_interval=0.1)
        
    @tornado.gen.coroutine
    def post(self):
        username, password = extract_credentials(self.json_request)

        while True:
            got_it = yield tornado.gen.Task(self.signup_lock.acquire, blocking=True)
            if got_it:
                break
            else:
                yield gen.sleep(10)

        inserted = yield tornado.gen.Task(
            self.redis_conn.setnx,
            username,
            auth.encrypt_password(password)
        )

        if inserted == 0:
            raise tornado.web.HTTPError(409, 'Such a username already exists')

        yield gen.Task(self.signup_lock.release)

        self.reply({
            'status': 'ok',
            'token': auth.generate_token(username).decode('ascii')
        }, status_code=201)


class SignInHandler(JSONHandler, RedisAwareHandler):
    @tornado.gen.coroutine
    def post(self):
        username, password = extract_credentials(self.json_request)

        stored_password = yield tornado.gen.Task(
            self.redis_conn.get,
            username
        )

        if (
            stored_password is not None and
            stored_password == auth.encrypt_password(password)
        ):
            self.reply({
                'status': 'ok',
                'token': auth.generate_token(username).decode('ascii')
            })
        else:
            raise tornado.web.HTTPError(401, 'Wrong password')


CHAT_REGISTRY = {}


chat_logger = logging.getLogger('chat')


def TRUTHY(*a):
    return True


class ChatHandler(tornado.websocket.WebSocketHandler):
    def get(self, token):
        if not token:
            auth_data = self.request.headers.get('authentication', '').split(' ')

            if len(auth_data) == 2 and auth_data[0] == 'Bearer':
                token = auth_data[1]
            else:
                raise tornado.web.HTTPError(401, 'Authentication failed')

        try:
            username = auth.authenticate(token)
        except Exception as e:
            logging.error(e)
            raise tornado.web.HTTPError(401)
        else:
            if username in CHAT_REGISTRY:
                raise tornado.web.HTTPError(403, 'Already logged in')
            else:
                self.current_user = username
            
        return super(ChatHandler, self).get()

    def select_subprotocol(self, protos):
        return 'minichat'

    def multicast(self, msg, condition=TRUTHY):
        for username, ws in CHAT_REGISTRY.items():
            if condition(username):
                ws.write_message(msg)

    def open(self):
        self.write_message({
            'type': 'participants',
            'from': 'chat',
            'content': list(CHAT_REGISTRY.keys())
        })

        self.to_others = lambda u: u != self.current_user

        CHAT_REGISTRY[self.current_user] = self
        chat_logger.info('%s joined the chat' % self.current_user)

        chat_msg = json.dumps({
            'type': 'login',
            'from': self.current_user
        })

        self.multicast(chat_msg, self.to_others)


    def on_message(self, message):
        chat_logger.info('%s: %s' % (self.current_user, message))

        try:
            message = json.loads(message)
        except Exception as e:
            logging.error(e)
        else:
            if message['type'] == 'message':
                to = message.get('to')

                chat_msg = json.dumps({
                    'type': 'message',
                    'content': message.get('content', ''),
                    'from': self.current_user,
                    'unicast': bool(to)
                })

                if to and to in CHAT_REGISTRY:
                    CHAT_REGISTRY[message['to']].write_message(chat_msg)
                else:
                    self.multicast(chat_msg, self.to_others)

    def on_close(self):
        chat_logger.info('%s has left the chat' % self.current_user)
        del CHAT_REGISTRY[self.current_user]

        chat_msg = json.dumps({
            'type': 'logout',
            'from': self.current_user
        })

        self.multicast(chat_msg, self.to_others)
