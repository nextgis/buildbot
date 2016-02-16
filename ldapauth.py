# -*- coding: utf-8 -*-

import ldap

from zope.interface import Interface
from zope.interface import implements

from buildbot.status.web.auth import IAuth
from buildbot.status.web.auth import AuthBase

class LdapAuth(AuthBase):
    implements(IAuth)
    """Implement basic authentication against a ldap."""
    lserver = ""
    base_dn = ""
    scope = ldap.SCOPE_SUBTREE
    group = ""

    def getUserInfo(self, user):
        l = ldap.initialize(self.lserver)
        l.set_option(ldap.OPT_REFERRALS, 0)
        l.protocol_version = 3
        filter = "(&(objectClass=posixAccount)(uid="+user+"))"
        results = l.search_s(self.base_dn, self.scope, filter)
        detailes = results[0][1]
        return dict(userName=user, fullName=detailes['displayName'][0], email=detailes['mail'][0], groups=[user])

    def __init__(self, lserver, bind, group):
        self.lserver = lserver
        self.base_dn = bind
        self.group = group

    def authenticate(self, user, passwd):
        l = ldap.initialize(self.lserver)
        l.set_option(ldap.OPT_REFERRALS, 0)
        l.protocol_version = 3

        filter = "(&(objectClass=posixAccount)(uid="+user+"))"
        groupFilter = '(&(cn='+self.group+')(memberUid=' +user+'))'

        #1. get user cn
        results = l.search_s(self.base_dn, self.scope, filter)
        for dn,entry in results:
            dn = str(dn)

        #2. check auth
        try:
            l.simple_bind_s(dn, passwd)
        except ldap.INVALID_CREDENTIALS:
            self.err = "Invalid credentials for " + user
            return False

        #3. check group
        results = l.search_s(base_dn, scope, groupFilter)

        if len(results) > 0:
            self.err = ""
            return True

        self.err = "Invalid username or password"
        return False
