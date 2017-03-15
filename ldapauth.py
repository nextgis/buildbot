# -*- coding: utf-8 -*-

import ldap
from twisted.cred.checkers import ICredentialsChecker
from twisted.cred.credentials import IUsernamePassword
from twisted.cred.error import UnauthorizedLogin
from twisted.internet import defer
from zope.interface.declarations import implements
from zope.interface import implementer
from twisted.cred.portal import Portal
from twisted.web.error import Error
from twisted.web.guard import BasicCredentialFactory
from twisted.web.guard import HTTPAuthSessionWrapper
from buildbot.www import auth
from buildbot.www import resource

class LDAPAuth(auth.AuthBase):

    def __init__(self, lserver, bind, group, **kwargs):
        self.credentialFactories = [BasicCredentialFactory("buildbot"),]
        self.checkers = [LDAPAuthChecker(lserver, bind, group),]
        self.userInfoProvider = LDAPUserInfoProvider(lserver, bind)

    def getLoginResource(self):
        return HTTPAuthSessionWrapper(
            Portal(auth.AuthRealm(self.master, self), self.checkers),
            self.credentialFactories)


class LDAPUserInfoProvider(auth.UserInfoProviderBase):
    name = "LDAP"
    lserver = ""
    base_dn = ""
    scope = ldap.SCOPE_SUBTREE

    def __init__(self, lserver, bind):
        self.lserver = lserver
        self.base_dn = bind

    def getUserInfo(self, username):
        l = ldap.initialize(self.lserver)
        l.set_option(ldap.OPT_REFERRALS, 0)
        l.protocol_version = 3
        filter = "(&(objectClass=posixAccount)(uid="+username+"))"
        results = l.search_s(self.base_dn, self.scope, filter)
        details = results[0][1]
        return defer.succeed(dict(userName=username, fullName=details['displayName'][0], email=details['mail'][0], groups=['buildbot', username]))


class LDAPAuthChecker():
    implements (ICredentialsChecker)

    credentialInterfaces = IUsernamePassword,

    lserver = ""
    base_dn = ""
    scope = ldap.SCOPE_SUBTREE
    group = ""


    def __init__(self, lserver, bind, group):
        self.lserver = lserver
        self.base_dn = bind
        self.group = group

    def requestAvatarId(self, credentials):
	l = ldap.initialize(self.lserver)
	l.set_option(ldap.OPT_REFERRALS, 0)
	l.protocol_version = 3

	filter = "(&(objectClass=posixAccount)(uid="+credentials.username+"))"
	groupFilter = '(&(cn='+self.group+')(memberUid=' +credentials.username+'))'

#	return defer.succeed(credentials.username)
	#1. get user cn
	results = l.search_s(self.base_dn, self.scope, filter)
	for dn,entry in results:
	    dn = str(dn)

    	#2. check auth
	l.simple_bind_s(dn, credentials.password)

    	#3. check group
	results = l.search_s(self.base_dn, self.scope, groupFilter)

	if len(results) > 0:
	    return defer.succeed(credentials.username)

        # Something went wrong. Simply fail authentication
        return defer.fail(UnauthorizedLogin("unable to verify password"))        
