import telebot, MySQLdb, json, requests, sys
from settings import host_bd
from settings import user_bd
from settings import password_bd
from settings import name_bd
from settings import name_table
from settings import bot_token
from settings import token
from settings import from_id

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

# ПОЛУЧЕНИЕ СПИСКА БАЛЛОВ
def convertDataLow(data):
    data = json.loads(data)
    return [data_array["Rate"] for data_array in data["response"]["Disciplines"]]

# ПОЛУЧЕНИЕ СПИСКА СУБМОДУЛЕЙ
def convertDataFull(data, token):
    data = json.loads(data)
    return [{"Id": data_array["ID"], "Name": data_array["SubjectName"], "Rate": data_array["Rate"], "Module": [{"NameModule": response["response"]["Submodules"][f"{data_subject}"]["Title"], "RateModule": response["response"]["Submodules"][f"{data_subject}"]["Rate"], "MaxRateModule": response["response"]["Submodules"][f"{data_subject}"]["MaxRate"]} for data_subject in response["response"]["Submodules"]]} for data_array in data["response"]["Disciplines"] for response in [json.loads(requests.get(f"https://grade.sfedu.ru/api/v1/student/discipline/subject?id={data_array['ID']}&token={token}").text)]]

bot = telebot.TeleBot(bot_token)
connect = bdConnect()

data = requests.get(f"https://grade.sfedu.ru/api/v1/student?token={token}").text
if data.find("Token is broken") != -1:
    bot.send_message(from_id, f"Токен неверный!")
    sys.exit()

data_low = json.dumps(convertDataLow(data))
data_full = json.dumps(convertDataFull(data, token))

request_bd = f"INSERT INTO `{name_table}` (`id`, `from_id`, `token`, `low`, `full`) VALUES (NULL, '{from_id}', '{token}', '{data_low}', '{data_full}');"
bdRequest(request_bd, connect)

bot.send_message(from_id, f"Вы были добавлены в систему бота!")