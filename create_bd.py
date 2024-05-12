import telebot, MySQLdb
from settings import host_bd
from settings import user_bd
from settings import password_bd
from settings import name_bd
from settings import name_table

# ПОДКЛЮЧЕНИЕ К БД
def bdConnect():
    MYSQLCONF = {'host': host_bd, 'user': user_bd, 'password': password_bd, 'db': name_bd, 'autocommit': True, 'charset': 'utf8'}
    connect = MySQLdb.connect(**MYSQLCONF)
    return connect

# ОТПРАВКА ЗАПРОСА К БД
def bdRequest(request, connect):
    cursor = connect.cursor()
    cursor.execute(request)
    row = cursor.fetchall()
    return row

request = f"CREATE TABLE `{name_table}` (`id` INT NOT NULL AUTO_INCREMENT, `from_id` VARCHAR(11) NOT NULL, `token` VARCHAR(45) NOT NULL, `low` LONGTEXT NULL, `full` LONGTEXT NULL, PRIMARY KEY (`id`)) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8 COLLATE = utf8_bin;"
bdRequest(request, bdConnect())