import ldap
import ldap.modlist as modlist
import config

lc = ldap.initialize('ldap://'+config.HOSTNAME+'/', trace_level=3)

lc.simple_bind_s(config.USERNAME, config.PASSWORD)

scope = ldap.SCOPE_SUBTREE
# filterexp = "(&(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2))(cn=*)(mail=*))"
attrlist = ['uid', 'displayName']

results = lc.search_s(config.BASE_DN, scope, config.DEPT_QUERY, attrlist)
for result in results:
    print(result[1]['uid'][0].decode("utf-8").rjust(35), result[1]['displayName'][0])

# # Some place-holders for old and new values
# old = {'mobile':["+555555"]}
# new = {'mobile':["+666666"]}
#
# # Convert place-holders for modify-operation using modlist-module
# ldif = modlist.modifyModlistmodlist.modifyModlist(old,new)
#
# # Do the actual modification
# lc.modify_s(config.BASE_DN, ldif)

# Its nice to the server to disconnect and free resources when done
lc.unbind_s()
