"""
    Normally, this file should not be under source control,
    but so it is for demonstration.
"""

WEBAPP_LOGGING_LEVEL = 'DEBUG'

WEBAPP_LOG_CONFIG = {
    'version': 1,
    'formatters': {
        'main': {
            'format': '%(levelname)-7s <%(name)-16s> [%(asctime)s] %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'main',

        }
    },
    'loggers': {
        'tornado.access': {
            'level': 'INFO',
            'propagate': True
        },
        'tornado.application': {
            'level': 'INFO',
            'propagate': True
        },
        'tornado.general': {
            'level': 'ERROR',
            'propagate': True
        },
        'chat': {
            'level': 'INFO',
            'propagate': True
        }

    },
    'root': {
        'handlers': ['console'],
        'level': WEBAPP_LOGGING_LEVEL
    },

}

PORT = 8888
SERVE_STATIC = True
STATIC_DIR = '/opt/minichat/cli'

SECRET = '^I$!sYimrs7Aq60UeBZ%HBGZCWb7igYvQKX5b9HbcgZkRF*TUo5IY^%5f^uQZVCi'
TOKEN_LIFETIME = 120000  # in seconds

REDIS_HOST = 'localhost'

