import ldap
import ldap.modlist as modlist
import config


class LdapModify:
    def __init__(self, hostname, username, password, trace_lvl=0):
        self.ldap_connect = ldap.initialize('ldap://'+hostname+'/', trace_level=trace_lvl)
        self.ldap_connect.simple_bind_s(username, password)
        self.scope = ldap.SCOPE_SUBTREE
        self.department = 'department'

    def get_member_dept(self, name, ou):
        filter_exp = config.USER_FILTER_TEMPLATE.format(name)
        base = config.BASE_DN_OU.format(ou)
        attr_list = [self.department]

        print('Name: {}'.format(name))
        try:
            results = self.ldap_connect.search_s(base, self.scope, filter_exp, attr_list)
        except ldap.NO_SUCH_OBJECT as err:
            # print('No results: {}'.format(err))
            return
        if results:
            department = self.check_department(results)
            if department:
                print(department+'\r\n')

    def modify_department(self):
        pass

    def check_department(self, results):
        try:
            department = results[0][1][self.department][0]
            department = department.decode("utf-8")
            return department
        except (IndexError, KeyError):
            return

    def get_group_members(self, group_ou):
        filter_exp = config.GROUP_MEMBERS_FILTER.format(group_ou)
        base = config.BASE_DN_GRP
        attr_list = ['member']
        members = ''
        results = self.ldap_connect.search_s(base, self.scope, filter_exp, attr_list)
        try:
            members = results[0][1][attr_list[0]]
        except KeyError as err:
            print('Cant get member of group: {}'.format(err))

        return [self.extract_user_name(member) for member in members]

    @property
    def get_groups(self):
        ou_grp_index = 0
        descr_grp_index = 1

        filter_exp = config.GROUP_FILTER
        attr_list = ['sAMAccountName', 'description']

        results = self.ldap_connect.search_s(config.BASE_DN_GRP, self.scope, filter_exp, attr_list)
        for result in results:
            group_ou = self.get_result_value(result, attr_list[ou_grp_index])
            group_description = self.get_result_value(result, attr_list[descr_grp_index])
            yield group_ou, group_description

    @staticmethod
    def get_result_value(result, name):
        try:
            value = result[1][name][0].decode("utf-8")
            return value
        except KeyError as err:
            print('Key error {}'.format(err))
            return None

    @staticmethod
    def extract_user_name(name):
        try:
            name = name.decode("utf-8")
            name = name.split(',')[0]
            name = name.split('=')[1]
        except IndexError as err:
            print('Cannot extract name: {}'.format(err))
            return False
        return name

    def __del__(self):
        self.ldap_connect.unbind_s()

    def modify_dept(self, value):
        old = {'department' : ['']}
        new = {'department' : ['']}
        ldif = modlist.modifyModlistmodlist.modifyModlist(old,new)
        self.ldap_connect.modify_s(config.BASE_DN, ldif)


def main():
    lc = LdapModify(config.HOSTNAME, config.USERNAME, config.PASSWORD)
    for group_ou, group_description in lc.get_groups:
        print('_____________________' * 5)
        print('OU: {}, Description: {}'.format(group_ou, group_description))
        members = lc.get_group_members(group_ou)
        for member in members:
            lc.get_member_dept(member, group_ou)
            # input()


if __name__ == '__main__':
    main()
