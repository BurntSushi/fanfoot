import ConfigParser
import json
import os
import os.path

import yql
import yql.storage

import fantasy

yqlconn = None

token_store = None

def connect():
    global yqlconn, token_store

    _cache_dir = os.path.join(fantasy.cur_dir, '.cache')
    _config = get_yql_config()

    _key = _config['key']
    _secret = _config['secret']
    _storage_key = _config['storage_key']

    if not os.access(_cache_dir, os.R_OK):
        os.mkdir(_cache_dir)
    token_store = yql.storage.FileTokenStore(_cache_dir, secret=_storage_key)

    yqlconn = yql.ThreeLegged(_key, _secret)

def get_stored_token():
    return token_store.get('mine')

def get_token():
    stored = get_stored_token()
    if not stored:
        req_token, auth_url = yqlconn.get_token_and_auth_url()
        print 'Go to: %s' % auth_url
        verifier = raw_input('Verifier: ')
        token = yqlconn.get_access_token(req_token, verifier)
        token_store.set('mine', token)
    else:
        token = yqlconn.check_token(stored)
        if token != stored:
            print 'Refreshing YAHOO token!'
            token_store.set('mine', token)

    return token

def yqlquery(sql):
    return yqlconn.execute(sql, token=get_token())

def get_yql_config(config_path=None):
    if config_path is None:
        config_path = os.path.join(fantasy.cur_dir, 'yql.ini')

    config = ConfigParser.RawConfigParser()
    config.readfp(open(config_path))
    return {
        'secret': config.get('yql', 'secret'),
        'key': config.get('yql', 'key'),
        'storage_key': config.get('yql', 'storage_key'),
    }

