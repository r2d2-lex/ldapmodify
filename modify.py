import ldap
import config
from datetime import datetime, timedelta


def ldap2datetime(ts):
    ts = int(ts)
    return datetime(1601, 1, 1) + timedelta(seconds=ts/10000000)


class LdapModify:
    def __init__(self, hostname, username, password, trace_lvl=0):
        self.ldap_connect = ldap.initialize('ldap://'+hostname+'/', trace_level=trace_lvl)
        self.ldap_connect.simple_bind_s(username, password)
        self.scope = ldap.SCOPE_SUBTREE
        self.department = 'department'

    def get_member_attrs(self, name, ou, *attrs) -> dict:
        filter_exp = config.USER_FILTER_TEMPLATE.format(name)
        base = config.BASE_DN_OU.format(ou)
        attr_list = [attr for attr in attrs]
        results_dict = {}
        try:
            results = self.ldap_connect.search_s(base, self.scope, filter_exp, attr_list)
        except ldap.NO_SUCH_OBJECT:
            return results_dict

        if results:
            for attr in attr_list:
                results_dict[attr] = self.check_attr(attr, results)
        return results_dict

    @staticmethod
    def check_attr(attr: str, results: list) -> str:
        try:
            result = results[0][1][attr][0]
            result = result.decode("utf-8")
            return result
        except (IndexError, KeyError):
            return ''

    def modify_department(self, dn, department_description):
        if not dn or not department_description:
            return False

        mod_list = [
            (ldap.MOD_REPLACE, self.department, department_description.encode('utf-8')),
        ]
        print('Modify dept to {}'.format(department_description))
        self.ldap_connect.modify_s(dn, mod_list)

    def remove_value_of_parameters(self, dn, *parameters):
        mod_list = [(ldap.MOD_DELETE, parm, None) for parm in parameters]
        try:
            self.ldap_connect.modify_s(dn, mod_list)
        except ldap.NO_SUCH_ATTRIBUTE as err:
            print('Error delete parameters {}: {}'.format(parameters, err))

    def get_group_members(self, group_ou) -> list:
        # return format: CN=Name_of_user,OU=Users,OU=Dept,DC=domain,DC=com
        filter_exp = config.GROUP_MEMBERS_FILTER.format(group_ou)
        base = config.BASE_DN_GRP
        attr_list = ['member']
        members = []
        results = self.ldap_connect.search_s(base, self.scope, filter_exp, attr_list)
        try:
            members = results[0][1][attr_list[0]]
        except (IndexError, KeyError) as err:
            print('Cant get member of group: {}'.format(err))
        return members

    @property
    def get_groups(self):
        ou_group_index = 0
        description_group_index = 1

        filter_exp = config.GROUP_FILTER
        attr_list = ['sAMAccountName', 'description']

        results = self.ldap_connect.search_s(config.BASE_DN_GRP, self.scope, filter_exp, attr_list)
        for result in results:
            group_ou = self.groups_result_value(result, attr_list[ou_group_index])
            group_description = self.groups_result_value(result, attr_list[description_group_index])
            yield group_ou, group_description

    @staticmethod
    def groups_result_value(result, name):
        try:
            value = result[1][name][0].decode("utf-8")
            return value
        except (IndexError, KeyError) as err:
            print('Key error {}'.format(err))
            return False

    def parse_dn(self, dn_user_name):
        user_name_parm = 0
        user_ou_parm = 2
        dn_user_name = dn_user_name.decode("utf-8")
        user_name = self.extract_parm(dn_user_name, user_name_parm)
        user_ou = self.extract_parm(dn_user_name, user_ou_parm)
        return user_name, user_ou

    @staticmethod
    def extract_parm(name, parm):
        try:
            value = name.split(',')[parm]
            value = value.split('=')[1]
        except IndexError as err:
            print('Cannot extract parm: {}'.format(err))
            return ''
        return value

    def __del__(self):
        self.ldap_connect.unbind_s()


def main():
    lc = LdapModify(config.HOSTNAME, config.USERNAME, config.PASSWORD)
    for group_ou, group_description in lc.get_groups:
        print('_____________________' * 5)
        print('OU: {}, Description: {}'.format(group_ou, group_description))
        members = lc.get_group_members(group_ou)
        for member in members:
            user_name, user_ou = lc.parse_dn(member)
            member_record = lc.get_member_attrs(user_name , user_ou, 'sAMAccountName', 'lastLogonTimestamp')
            if member_record:
                print('{}, ou: {}'.format(user_name, user_ou))
                for key in member_record:
                    print('{}: {}'.format(key, member_record[key]))
                    if key == 'lastLogonTimestamp':
                        print(ldap2datetime(member_record[key]).isoformat())
                print('\r\n')


if __name__ == '__main__':
    main()
