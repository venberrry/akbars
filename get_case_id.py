import re
import requests
import time
from datetime import datetime


def name_birthsday_parser(search_value : str) -> (str, str) :
    """
    Парсер входных данных на имя и дату рождения
    Возвращает ФИО и дату рождения в формате "ДД.ММ.ГГГГ"
    """
    name = re.sub(r"[^а-яА-Яa-zA-Z ]", "", search_value)
    name = " ".join(name.split())
    match = re.search(r"\b\d{2}\.\d{2}\.\d{4}\b$", search_value)
    if match:
        date = match.group()
    else:
        raise ValueError("Ошибка: введена неправильная дата рождения. Формат должен быть ДД.ММ.ГГГГ")
    return name, date


def find_all_guid_matches(data:list) -> list[str]:
    """
    Парсинг json со всеми пришедшими совпадениями по имени
    """
    return [person["guid"] for person in data.get("pageData", [])]


def link_generator(guids:list) -> list[str]:
    """
    Создание ссылок для запроса к API по GUID
    """
    return [f"https://fedresurs.ru/persons/{guid}" for guid in guids]

def birthday_check(raw_date: str, target_date: str) -> bool:
    """
    Проверяет, совпадает ли дата рождения из API с запрашиваемой датой
    """
    if not raw_date:
        return False
    try:
        return datetime.strptime(raw_date[:10], "%Y-%m-%d").strftime("%d.%m.%Y") == target_date
    except ValueError:
        return False

def get_cases(links:list[str], target_birthday: str)-> dict:
    """
    Запрашивает данные по списку ссылок на профили банкротов
    """
    print("Ищем...")

    results = {}

    while links:
        base_url = links.pop()
        main_url = base_url.replace("persons", "backend/persons") + "/main"
        bankruptcy_url = base_url.replace("persons", "backend/persons") + "/bankruptcy"
        birthday_url = base_url.replace("persons", "backend/persons")
        try:
            # Запрос ФИО
            name_response = requests.get(main_url, headers={**headers_xhr, "Referer": "https://fedresurs.ru/persons/"})
            if name_response.status_code == 200:
                person_name = name_response.json().get("name", "Имя не найдено")
            else:
                continue

            # Проверка даты рождения (Закоментировать блок если это не важно)
            birthday_response = requests.get(birthday_url, headers={**headers_xhr, "Referer": "https://fedresurs.ru/persons/"})
            if birthday_response.status_code != 200:
                continue
            person_birthday = birthday_response.json().get("birthdateBankruptcy", None)

            if not birthday_check(person_birthday, target_birthday):
                continue  # Пропускаем профиль, если дата не совпала

            # Запрос номеров дел о бранкротстве (в т.ч нескольких, если есть)
            cases_response = requests.get(bankruptcy_url, headers={**headers_xhr, "Referer": "https://fedresurs.ru/persons/"})
            case_numbers = []
            if cases_response.status_code == 200:
                data = cases_response.json()
                case_numbers = [case["number"] for case in data.get("legalCases", [])]

            # Записываем результат
            results[person_name] = case_numbers if case_numbers else ["Нет дел о банкротстве"]

            # Пауза между запросами от бана
            time.sleep(1.5)

        except Exception as e:
            print(f"Ошибка при обработке {base_url}: {e}")

    return results


search_value = input("Введите ФИО и дату рождения в формате :'Абв Где Еж ДД.ММ.ГГГГ'\n")

bankrupts_name, bankrupts_bithsday = name_birthsday_parser(search_value)
disqualificants_url = f"https://bankrot.fedresurs.ru/bankrupts?searchString={bankrupts_name}&regionId=all&isActiveLegalCase=null&offset=0&limit=15"
xhr_url = "https://bankrot.fedresurs.ru/backend/prsnbankrupts"
headers_xhr = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "Referer": "https://bankrot.fedresurs.ru/bankrupts",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://bankrot.fedresurs.ru",
            "X-Requested-With": "XMLHttpRequest"
}
params = {
    "searchString": f"{bankrupts_name}",  # ФИО банкрота
    "isActiveLegalCase": "null",
    "limit": 15,
    "offset": 0
}
try:
    response = requests.get(xhr_url, headers=headers_xhr, params=params)
    if response.status_code == 200:
        try:
            data = response.json()
            guids_list = find_all_guid_matches(data)
            if not guids_list:
                print("Ошибка: банкротов с таким именем не найдено. Проверьте ввод и повторите попытку")
                exit(1)
            profile_links = link_generator(guids_list)
            bankrupts_cases = get_cases(profile_links, bankrupts_bithsday)
            if not bankrupts_cases:
                print("Человека с такой датой рождения нет в ЕФРСБ. Проверьте ввод")
            for name, cases in bankrupts_cases.items():
                print(f"{name} — {cases}")
        except requests.exceptions.JSONDecodeError:
            print("Ошибка: сервер не вернул JSON")
    else:
        print(f"Ошибка {response.status_code}:", response.text)
except requests.exceptions.RequestException as e:
    print("Сервис недоступен")