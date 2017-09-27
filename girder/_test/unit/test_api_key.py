#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import datetime
import json
import pytest
import six

from girder.constants import SettingKey, TokenScope
from girder.models.model_base import ValidationException
from girder._test.assertions import assertStatus, assertStatusOk


def testListScopes(server):
    resp = server.request('/token/scopes')
    assertStatusOk(resp)
    assert resp.json == TokenScope.listScopes()

    assert 'custom' in resp.json
    assert isinstance(resp.json['custom'], list)
    assert 'adminCustom' in resp.json
    assert isinstance(resp.json['adminCustom'], list)

    for scope in resp.json['custom'] + resp.json['adminCustom']:
        assert 'id' in scope
        assert 'name' in scope
        assert 'description' in scope


def testListKeys(server, admin, user):
    # Normal users shouldn't be able to request other users' keys
    resp = server.request('/api_key', params={'userId': admin['_id']},
                        user=user)
    assertStatus(resp, 403)
    assert resp.json['message'] == 'Administrator access required.'

    # Users should be able to request their own keys
    resp = server.request('/api_key', params={'userId': user['_id']},
                        user=user)
    assertStatusOk(resp)
    assert resp.json == []

    # Passing no user ID should work
    resp = server.request('/api_key', user=user)
    assertStatusOk(resp)
    assert resp.json == []

    # Admins should be able to see other users' keys
    resp = server.request('/api_key', params={'userId': user['_id']},
                        user=admin)
    assertStatusOk(resp)
    assert resp.json == []

def testKeyPolicies(server, model, user):
    defaultDuration = model('setting').get(SettingKey.COOKIE_LIFETIME)
    # Create a new API key with full access
    resp = server.request('/api_key', method='POST', params={
        'name': 'test key'
    }, user=user)
    assertStatusOk(resp)
    apiKey = model('api_key').load(resp.json['_id'], force=True)
    assert apiKey['scope'] == None
    assert apiKey['name'] == 'test key'
    assert apiKey['lastUse'] == None
    assert apiKey['tokenDuration'] == None
    assert apiKey['active'] == True

    # Create a token using the key
    resp = server.request('/api_key/token', method='POST', params={
        'key': apiKey['key'],
        'duration': defaultDuration + 1000
    })
    assertStatusOk(resp)
    token = model('token').load(
        resp.json['authToken']['token'], force=True, objectId=False)
    # Make sure token has full user auth access
    assert token['userId'] == user['_id']
    assert token['scope'] == [TokenScope.USER_AUTH]
    # Make sure the token references the API key used to create it
    assert token['apiKeyId'] == apiKey['_id']

    # Make sure the token duration is not longer than the default
    duration = token['expires'] - token['created']
    assert duration == \
                     datetime.timedelta(days=defaultDuration)

    # We should be able to request a duration shorter than default
    resp = server.request('/api_key/token', method='POST', params={
        'key': apiKey['key'],
        'duration': defaultDuration - 1
    })
    assertStatusOk(resp)
    token = model('token').load(
        resp.json['authToken']['token'], force=True, objectId=False)
    duration = token['expires'] - token['created']
    assert duration == \
                     datetime.timedelta(days=defaultDuration - 1)

    # We should have two tokens for this key
    q = {
        'userId': user['_id'],
        'apiKeyId': apiKey['_id']
    }
    count = model('token').find(q).count()
    assert count == 2

    # Deactivate the key and change the token duration and scope
    newScopes = [TokenScope.DATA_READ, TokenScope.DATA_WRITE]
    resp = server.request('/api_key/%s' % apiKey['_id'], params={
        'active': False,
        'tokenDuration': 10,
        'scope': json.dumps(newScopes)
    }, method='PUT', user=user)
    assertStatusOk(resp)
    # Make sure key itself didn't change
    assert resp.json['key'] == apiKey['key']
    apiKey = model('api_key').load(resp.json['_id'], force=True)
    assert apiKey['active'] == False
    assert apiKey['tokenDuration'] == 10
    assert set(apiKey['scope']) == set(newScopes)
    # Should now have a last used timestamp
    assert isinstance(apiKey['lastUse'], datetime.datetime)

    # This should have deleted all corresponding tokens
    q = {
        'userId': user['_id'],
        'apiKeyId': apiKey['_id']
    }
    count = model('token').find(q).count()
    assert count == 0

    # We should not be able to create tokens for this key anymore
    resp = server.request('/api_key/token', method='POST', params={
        'key': apiKey['key']
    })
    assertStatus(resp, 400)
    assert resp.json['message'] == 'Invalid API key.'

    # Reactivate key
    resp = server.request('/api_key/%s' % apiKey['_id'], params={
        'active': True
    }, method='PUT', user=user)
    assertStatusOk(resp)
    assert resp.json['key'] == apiKey['key']
    apiKey = model('api_key').load(resp.json['_id'], force=True)

    # Should now be able to make tokens with 10 day duration
    resp = server.request('/api_key/token', method='POST', params={
        'key': apiKey['key']
    })
    assertStatusOk(resp)
    token = model('token').load(
        resp.json['authToken']['token'], force=True, objectId=False)
    duration = token['expires'] - token['created']
    assert duration == datetime.timedelta(days=10)
    assert set(token['scope']) == set(newScopes)

    # Deleting the API key should delete the tokens made with it
    count = model('token').find(q).count()
    assert count == 1
    resp = server.request('/api_key/%s' % apiKey['_id'], method='DELETE', user=user)
    assertStatusOk(resp)
    count = model('token').find(q).count()
    assert count == 0

def testScopeValidation(db, model, admin, user):
    # Make sure normal user cannot request admin scopes
    requestedScopes = [TokenScope.DATA_OWN, TokenScope.SETTINGS_READ]

    with pytest.raises(ValidationException, match='Invalid scopes: %s.$' %
                       TokenScope.SETTINGS_READ):
        model('api_key').createApiKey(user=user, name='', scope=requestedScopes)

    # Make sure an unregistered scope cannot be set on an API key
    requestedScopes = [TokenScope.DATA_OWN, TokenScope.SETTINGS_READ, 'nonsense']

    with pytest.raises(ValidationException, match='Invalid scopes: nonsense.$'):
        model('api_key').createApiKey(user=admin, name='', scope=requestedScopes)
