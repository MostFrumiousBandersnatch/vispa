import jwt
import datetime
import hashlib
import hmac

import conf

def generate_token(username):
    now = int(datetime.datetime.utcnow().timestamp())

    return jwt.encode(
        {
            'name': username,
            'iat': now,
            'exp': now + conf.TOKEN_LIFETIME
        },
        conf.SECRET,
        algorithm='HS256'
    )


def authenticate(token):
    return jwt.decode(token, conf.SECRET)['name']


def encrypt_password(password):
    return hmac.new(
        conf.SECRET.encode('ascii'),
        password.encode('utf8'),
        digestmod=hashlib.sha1
    ).hexdigest()


