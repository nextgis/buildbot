# -*- coding: utf-8 -*-

import ldap
from twisted.cred.checkers import ICredentialsChecker
from twisted.cred.credentials import IUsernamePassword
from twisted.cred.error import UnauthorizedLogin
from twisted.internet import defer

# from zope.interface import implements
from zope.interface import implementer
from twisted.cred.portal import Portal

# from twisted.web.error import Error
from twisted.web.guard import BasicCredentialFactory
from twisted.web.guard import HTTPAuthSessionWrapper
from buildbot.www import auth

# from buildbot.www import resource
from twisted.python import log


class LDAPAuth(auth.AuthBase):
    def __init__(self, lserver, base_dn, binddn, bindpwd, group, **kwargs):
        self.credentialFactories = [
            BasicCredentialFactory("buildbot"),
        ]
        self.checkers = [
            LDAPAuthChecker(lserver, base_dn, binddn, bindpwd, group),
        ]
        self.userInfoProvider = LDAPUserInfoProvider(lserver, base_dn, binddn, bindpwd)

    def getLoginResource(self):
        return HTTPAuthSessionWrapper(
            Portal(auth.AuthRealm(self.master, self), self.checkers),
            self.credentialFactories,
        )


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
            fullName = str(details["cn"][0], "utf-8", "ignore")
            email = str(details["mail"][0], "utf-8", "ignore")
            return defer.succeed(
                dict(
                    userName=username,
                    fullName=fullName,
                    email=email,
                    groups=["buildbot", username],
                )
            )
        except ldap.LDAPError as e:
            log.msg("LDAP Error: {0}".format(str(e)))

        # Something went wrong. Simply fail authentication
        log.msg("LDAP Error: Unable to get user information")
        return defer.fail(UnauthorizedLogin("Unable to get user information"))


@implementer(ICredentialsChecker)
class LDAPAuthChecker:
    credentialInterfaces = (IUsernamePassword,)

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
            username = str(credentials.username, "utf-8", "ignore")
            password = str(credentials.password, "utf-8", "ignore")
            filter = "(&(objectClass=posixAccount)(uid=" + username + "))"
            groupFilter = "(&(cn=" + self.group + ")(memberUid=" + username + "))"

            # 1. get user cn
            results = l.search_s(self.base_dn, self.scope, filter)
            user_dn = ""
            for dn, entry in results:
                user_dn = str(dn)
                break
            if not user_dn:
                log.msg("LDAP Error: Unable to verify user")
                return defer.fail(UnauthorizedLogin("Unable to verify user"))

            results = l.search_s(self.base_dn, self.scope, groupFilter)
            in_group = len(results) > 0

            # 2. check auth
            l.simple_bind_s(user_dn, password)

            # 3. check group
            if in_group:
                return defer.succeed(username)

        except ldap.LDAPError as e:
            log.msg("LDAP Error: {0}".format(str(e)))

        # Something went wrong. Simply fail authentication
        log.msg("LDAP Error: Unable to verify password or user is not in group")
        return defer.fail(UnauthorizedLogin("Unable to verify password"))
