import config
import psycopg2
from contextlib import closing
from LdapModify import LdapModify


def datetime_to_str(date_time):
    dt = LdapModify.ldap2datetime(date_time)
    return dt.strftime("%Y-%m-%d")


def main():
    all_users_dict = {}
    user_attrs = ['lastLogonTimestamp', 'physicalDeliveryOfficeName']

    lc = LdapModify(config.HOSTNAME, config.USERNAME, config.PASSWORD)
    for group_ou, group_description in lc.get_groups(config.BASE_DN_GRP, config.GROUP_FILTER):
        group_members = lc.get_group_members(config.BASE_DN_GRP, config.GROUP_MEMBERS_FILTER.format(group_ou))
        users_dict = lc.make_members_dict(config.BASE_DN_OU, config.USER_FILTER_TEMPLATE, group_members, *user_attrs)
        all_users_dict = {**all_users_dict, **users_dict}

    print('Всего {} пользователей\r\n'.format(len(all_users_dict)))

    # Connect to PG_Base
    with closing(open_database()) as connect:
        with connect.cursor() as db_cursor:
            get_users_info('userlist.txt', all_users_dict, db_cursor)


def open_database():
    con = psycopg2.connect(
        database=config.PG_DATABASE,
        user=config.PG_USER,
        password=config.PG_PASSWORD,
        host=config.PG_HOST,
        port=config.PG_PORT,
    )
    print("Database opened successfully")
    return con


def get_pgdb_user_room(cursor, login):
    cursor.execute('SELECT room FROM users WHERE login LIKE \'{}\' LIMIT 1;'.format(login))
    try:
        room = cursor.fetchone()[0]
    except (IndexError, TypeError):
        return ''
    if not room:
        return ''
    return room


def get_users_info(filename, users_dict, cursor):
    with open(filename) as fh:
        login_names = fh.read().splitlines()
    for login in login_names:
        if login in users_dict:
            user_record = users_dict[login]
            result_string = ''
            for key, value in user_record.items():
                if key == 'lastLogonTimestamp':
                    value = datetime_to_str(value)
                result_string += '{};'.format(value)
            # result_string += '{};'.format(get_pgdb_user_room(cursor, login))
            print(result_string)
        else:
            print('*** Нет записи для логина: "{}" в словаре!'.format(login))


if __name__ == '__main__':
    main()
