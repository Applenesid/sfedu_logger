import telebot, MySQLdb, json, requests
from settings import host_bd
from settings import user_bd
from settings import password_bd
from settings import name_bd
from settings import name_table
from settings import bot_token

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
    return [data_array["Rate"] for data_array in data["response"]["Disciplines"]]

# ПОЛУЧЕНИЕ СПИСКА СУБМОДУЛЕЙ
def convertDataFull(data, token):
    return [{"Id": data_array["ID"], "Name": data_array["SubjectName"], "Rate": data_array["Rate"], "Module": [{"NameModule": response["response"]["Submodules"][f"{data_subject}"]["Title"], "RateModule": response["response"]["Submodules"][f"{data_subject}"]["Rate"], "MaxRateModule": response["response"]["Submodules"][f"{data_subject}"]["MaxRate"]} for data_subject in response["response"]["Submodules"]]} for data_array in data["response"]["Disciplines"] for response in [json.loads(requests.get(f"https://grade.sfedu.ru/api/v1/student/discipline/subject?id={data_array['ID']}&token={token}").text)]]

# СВЕРКА ЗНАЧЕНИЙ БАЛЛОВ
def checkRate(data_req, data_bd):
    return [rate_bd[0] for rate_bd in enumerate(json.loads(data_bd)) if rate_bd[1] != data_req[rate_bd[0]]]

# ПОИСК РАСХОЖДЕНИЙ В БАЛЛАХ
def checkModule(data_req, data_bd, index):
    return [{"Name": data_req[i]["Name"], "Rate": data_req[i]["Rate"], "NameModule": data_req[i]["Module"][n]["NameModule"], "RateModule": data_req[i]["Module"][n]["RateModule"], "MaxRateModule": data_req[i]["Module"][n]["MaxRateModule"], "RateDiff": (f"+{rate_diff}" if rate_diff >= 0 else f"–{abs(rate_diff)}")} for i in index for n, data_index in enumerate(json.loads(data_bd)[i]["Module"]) if data_index["RateModule"] != data_req[i]["Module"][n]["RateModule"] for rate_diff in [int(0 if data_req[i]["Module"][n]["RateModule"] is None else data_req[i]["Module"][n]["RateModule"]) - int(0 if data_index["RateModule"] is None else data_index["RateModule"])]]

bot = telebot.TeleBot(bot_token)
connect = bdConnect()

for data_row in bdRequest(f"SELECT * FROM `{name_table}`", connect):
    data_req = json.loads(requests.get(f"https://grade.sfedu.ru/api/v1/student?token={data_row[2]}").text)
    index = checkRate(convertDataLow(data_req), data_row[3])
    if index:
        module = checkModule(convertDataFull(data_req, data_row[2]), data_row[4], index)
        for message in module:
            bot.send_message(data_row[1], f"✅ <b>ИЗМЕНЕНИЯ В БАЛЛАХ!</b>\n\n<b>Предмет:</b> {message['Name']}\n<b>Модуль:</b> {message['NameModule']}\n\n<b>Баллы:</b> {int(0 if message['RateModule'] is None else message['RateModule'])} / {int(0 if message['MaxRateModule'] is None else message['MaxRateModule'])}  [{message['RateDiff']}]\n<b>Всего:</b> {int(0 if message['Rate'] is None else message['Rate'])} / 100", parse_mode="HTML")
            request = f"UPDATE `{name_table}` SET `full` = '{json.dumps(convertDataFull(data_req, data_row[2]))}', `low` = '{json.dumps(convertDataLow(data_req))}' WHERE `{name_table}`.`id` = {data_row[0]}; "
            bdRequest(request, connect)

connect.close()