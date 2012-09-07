import json
import os
import os.path

import yql
import yql.storage

_cur_dir = os.path.split(__file__)[0]
_json_secrets = os.path.join(_cur_dir, 'yql.json')
_cache_dir = os.path.join(_cur_dir, '.cache')
_secrets = json.loads(open(_json_secrets).read())

_key = _secrets['key']
_secret = _secrets['secret']
_store_key = _secrets['store_key']

if not os.access(_cache_dir, os.R_OK):
    os.mkdir(_cache_dir)
token_store = yql.storage.FileTokenStore(_cache_dir, secret=_store_key)

y = yql.ThreeLegged(_key, _secret)

def get_stored_token():
    return token_store.get('mine')

def get_token():
    stored = get_stored_token()
    if not stored:
        req_token, auth_url = y.get_token_and_auth_url()
        print 'Go to: %s' % auth_url
        verifier = raw_input('Verifier: ')
        token = y.get_access_token(req_token, verifier)
        token_store.set('mine', token)
    else:
        token = y.check_token(stored)
        if token != stored:
            print 'Refreshing YAHOO token!'
            token_store.set('mine', token)

    return token

def yqlquery(sql):
    return y.execute(sql, token=get_token())

