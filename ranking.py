import requests
import operator
import base64
import config

def get_session_token():
  """Obter um token para acesso ao GLPi."""

  res = requests.get(
    "%s/apirest.php/initSession" % config.GLPI_BASE_URL,
    params={},
    headers={
      "Content-Type": "application/json",
      "App-Token": config.GLPI_TOKEN
    },
    auth=(
      config.GLPI_LOGIN_USER,
      config.GLPI_TOKEN_PASSWORD
    )
  )

  json = res.json()
  session_token = json["session_token"]

  return session_token

def get_user_production(session_token, user_id):
  """Obter o número de chamados fechados por um determinado usuário."""

  res = requests.get(
    "%s/apirest.php/search/Ticket" % config.GLPI_BASE_URL,
    params={
      "is_deleted": "0",
      "criteria[0][field]": "16",
      "criteria[0][searchtype]": "equals",
      "_select_criteria[0][value]": "TODAY",
      "criteria[0][value]": "TODAY",
      "criteria[1][link]": "AND",
      "criteria[1][field]": "64",
      "criteria[1][searchtype]": "equals",
      "criteria[1][value]": user_id
    },
    headers={
      "Content-Type": "application/json",
      "App-Token": config.GLPI_TOKEN,
      "Session-Token": session_token
    }
  )

  json = res.json()
  totalcount = json["totalcount"]

  return totalcount

def send_message(message, chat_id):
  """Enviar mensagem para o Telegram de alguém."""

  res = requests.post(
    "https://api.telegram.org/bot%s/sendMessage" % config.TG_TOKEN,
    headers={
      "Content-Type": "application/json"
    },
    json={
      "text": message,
      "chat_id": chat_id,
      "parse_mode": "markdown"
    }
  )

def send_messages(message, chat_ids):
  """Enviar mensagem para o Telegram de várias pessoas."""

  for chat_id in chat_ids:
    send_message(message, chat_id)

def build_telegram_message(data):
  """Construir mensagem que será enviada no Telegram (em Markdown)."""
  message = ""

  for information in data:
    index = "`(%sº)`" % information["index"]
    name = "[%s](%s/front/user.form.php?id=%i)" % (information["name"],
      config.GLPI_BASE_URL, information["id"])
    score = information["score"]
    
    message += "%s %s → %d\n" % (index, name, score)

  return message

def get_ranking_data(session_token, data):
  """Obter dados dados do ranking."""

  for i in range(len(data)):
    user_production = get_user_production(session_token, data[i]["id"])

    data[i]["score"] = user_production

  data = list(reversed(sorted(data, key=operator.itemgetter("score"))))

  for i in range(len(data)):
    if (i > 0 and data[i]["score"] == data[i - 1]["score"]):
      data[i]["index"] = data[i - 1]["index"]
    else:
      if (i == 0):
        data[i]["index"] = 1
      else:
        data[i]["index"] = data[i - 1]["index"] + 1

  return data

if (__name__ == "__main__"):
  session_token = get_session_token()
  ranking_data = get_ranking_data(session_token, config.GLPI_USERS)
  telegram_message = build_telegram_message(ranking_data)

  send_messages(telegram_message, config.TG_CHAT_IDS)