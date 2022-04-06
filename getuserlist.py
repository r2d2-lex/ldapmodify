import config
from LdapModify import LdapModify


def get_user_list():
    """
    :return: Example: UserFIO:  {'displayName': 'User Display Name', 'uidNumber': '5555', 'sAMAccountName': 'UserFIO'}
    """
    all_users_dict = {}
    user_attrs = ['uidNumber', ]

    lc = LdapModify(config.HOSTNAME, config.USERNAME, config.PASSWORD)
    for group_ou, group_description in lc.get_groups(config.BASE_DN_GRP, config.GROUP_FILTER):
        # print('OU: {}, Description: {}'.format(group_ou, group_description))
        group_members = lc.get_group_members(config.BASE_DN_GRP, config.GROUP_MEMBERS_FILTER.format(group_ou))
        users_dict = lc.make_members_dict(config.BASE_DN_OU, config.USER_FILTER_TEMPLATE, group_members, *user_attrs)
        all_users_dict = {**all_users_dict, **users_dict}
    return all_users_dict


def make_users_dict(users_dict: dict):
    """
        Создаёт словарь с ключом uidNumber значением sAMAccountName
    :param users_dict:
    :return:
    """
    result_dict = {}
    for value in users_dict.values():
        result_dict[value['uidNumber']] = value['sAMAccountName']
    return result_dict


def check_uid(uid, user_dict):
    """
        Проверяет присутствие uid из словаря make_users_dict. Возвращает  sAMAccountName
    :param uid:
    :param user_dict:
    :return:
    """
    name = user_dict.get(uid, 'Not Found')
    return name


def main():
    user_dict = make_users_dict(get_user_list())
    print(user_dict)
    print(check_uid('1234', user_dict))


if __name__ == '__main__':
    main()
