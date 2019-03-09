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

    def __init__(self, lserver, base_dn, binddn, bindpwd, group, **kwargs):
        self.credentialFactories = [BasicCredentialFactory("buildbot"),]
        self.checkers = [LDAPAuthChecker(lserver, base_dn, binddn, bindpwd, group),]
        self.userInfoProvider = LDAPUserInfoProvider(lserver, base_dn, binddn, bindpwd)

    def getLoginResource(self):
        return HTTPAuthSessionWrapper(
            Portal(auth.AuthRealm(self.master, self), self.checkers),
            self.credentialFactories)

class LDAPUserInfoProvider(auth.UserInfoProviderBase):
    name = "LDAP"
    lserver = ""
    base_dn = ""
    binddn = ""
    bindpwd = ""
    scope = ldap.SCOPE_SUBTREE

    def __init__(self, lserver, base_dn, binddn, bindpwd):
        self.lserver = lserver
        self.base_dn = base_dn
        self.binddn = binddn
        self.bindpwd = bindpwd

    def getUserInfo(self, username):
        try:
            l = ldap.initialize(self.lserver)
            l.set_option(ldap.OPT_REFERRALS, 0)
            l.protocol_version = 3
            l.simple_bind_s(self.binddn, self.bindpwd)
            filter = "(&(objectClass=posixAccount)(uid=" + username + "))"
            results = l.search_s(self.base_dn, self.scope, filter)
            details = results[0][1]
            return defer.succeed(dict(userName=username, fullName=details['displayName'][0], email=details['mail'][0], groups=['buildbot', username]))
        except ldap.LDAPError as e:
            print('LDAP Error: {0}'.format(e.message['desc'] if 'desc' in e.message else str(e)))

        # Something went wrong. Simply fail authentication
        return defer.fail(UnauthorizedLogin("Unable to verify password"))

@implementer(ICredentialsChecker)
class LDAPAuthChecker():

    credentialInterfaces = IUsernamePassword,

    lserver = ""
    base_dn = ""
    binddn = ""
    bindpwd = ""
    scope = ldap.SCOPE_SUBTREE
    group = ""


    def __init__(self, lserver, base_dn, binddn, bindpwd, group):
        self.lserver = lserver
        self.base_dn = base_dn
        self.binddn = binddn
        self.bindpwd = bindpwd
        self.group = group

    def requestAvatarId(self, credentials):
        try:
            l = ldap.initialize(self.lserver)
            l.set_option(ldap.OPT_REFERRALS, 0)
            l.protocol_version = 3
            l.simple_bind_s(self.binddn, self.bindpwd)
            username = credentials.username.encode("utf-8")
            filter = "(&(objectClass=posixAccount)(uid=" + username + "))"
            groupFilter = "(&(cn=" + self.group + ")(memberUid=" + username + "))"

            # return defer.succeed(credentials.username)
            #1. get user cn
            results = l.search_s(self.base_dn, self.scope, filter)
            for dn,entry in results:
                dn = str(dn)
            results = l.search_s(self.base_dn, self.scope, groupFilter)
            in_group = len(results) > 0

            #2. check auth
            l.simple_bind_s(dn, credentials.password)

            #3. check group
            if in_group:
                return defer.succeed(credentials.username)

        except ldap.LDAPError as e:
            print('LDAP Error: {0}'.format(e.message['desc'] if 'desc' in e.message else str(e)))

        # Something went wrong. Simply fail authentication
        return defer.fail(UnauthorizedLogin("Unable to verify password"))
