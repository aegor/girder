import pytest
import random

from girder.constants import TokenScope
from girder.models.model_base import AccessException
from girder.models.token import genToken
from girder._test.assertions import *


def testCryptographicSecurity():
    # Make sure we are not using the normal random to generate tokens
    random.seed(1)
    token1 = genToken()
    random.seed(1)
    token2 = genToken()

    assert token1 != token2


def testHasScope(db, model):
    scope = TokenScope.DATA_READ
    tokenModel = model('token')
    token = tokenModel.createToken(scope=scope)

    # If token is None should return False
    assert not tokenModel.hasScope(None, scope)

    # If scope is None should return True
    assert tokenModel.hasScope(token, None)


def testRequireScope(db, model):
    scope = TokenScope.DATA_OWN
    anotherScope = TokenScope.SETTINGS_READ
    tokenModel = model('token')
    token = tokenModel.createToken(scope=scope)

    # If specified scope does not exist raise an error
    with pytest.raises(AccessException):
        tokenModel.requireScope(token, anotherScope)


def testGetAndDeleteSession(server):
    resp = server.request(path='/token/session', method='GET')
    assertStatusOk(resp)
    token = resp.json['token']
    # If we ask for another token, we should get a differnt one
    resp = server.request(path='/token/session', method='GET')
    assertStatusOk(resp)
    token2 = resp.json['token']
    assert token != token2
    # If we ask for another token, passing in the first one, we should get
    # the first one back
    resp = server.request(path='/token/session', method='GET', token=token)
    assertStatusOk(resp)
    token2 = resp.json['token']
    assert token == token2
    # If we ask about the current token without passing one, we should get
    # null
    resp = server.request(path='/token/current', method='GET')
    assertStatusOk(resp)
    assert resp.json == None
    # With a token, we get the token document in the response
    resp = server.request(path='/token/current', method='GET', token=token)
    assertStatusOk(resp)
    assert token == resp.json['_id']
    # Trying to delete a token without specifying one results in an error
    resp = server.request(path='/token/session', method='DELETE')
    assertStatus(resp, 401)
    # With the token should succeed
    resp = server.request(path='/token/session', method='DELETE', token=token)
    assertStatusOk(resp)
    # Now the token is gone, so it should fail
    resp = server.request(path='/token/session', method='DELETE', token=token)
    assertStatus(resp, 401)
