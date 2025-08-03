import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import argparse


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

session = requests.Session() # сессия с логином

# функция входа в аккаунт (для отображения заказчика)
def login():
    link = 'https://rostender.info/login'
    data = {
        'username': 'nlbeglov',
        'password': '58LQUWcv',
        'rememberMe': '0',
        'termsAgree': '1',

    }
    response = session.post(link, data=data, headers=HEADERS)
    if 'nlbeglov' in response.text:
        print("Успешный вход в аккаунт!")
        return True
    else:
        print("Ошибка входа в аккаунт!")
        return False

# функция получения страницы
def get_html(url):
    try:
        response = session.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f'[Ошибка запроса] {e}')
        return None

# парсинг ссылок на все тендеры
def get_links(max_count):
    links = []
    print('Поиск тендеров...')
    count = 1
    while count < max_count:
        html = get_html('https://rostender.info/extsearch?page=' + str(count))
        soup = BeautifulSoup(html, 'html.parser')
        link_tags = soup.select('a.description')
        for tag in link_tags:
            href = tag.get('href')
            if href:
                full_url = f'https://rostender.info{href}'
                links.append(full_url)
                count += 1
                if count > max_count:
                    break

    print(f'Найдено {len(links)} ссылок')
    return links


# парсинг каждой страницы с тендерами по отдельности
def parse_data(html):
    data = {}
    soup = BeautifulSoup(html, 'html.parser')

    # получение заказчика
    customer = soup.find(
        'div',
        attrs={'data-id': re.compile(r'^customer_')},
        class_='line-clamp line-clamp--n5'
    )
    try:
        customer = customer.text.strip()
    except AttributeError:
        customer = "-"
    data['Заказчик'] = customer

    # получение номера
    number = soup.find('div', class_='tender-info-header-number').text.strip()
    match = re.search(r'№\s*(\d+)', number)
    tender_number = match.group(1)
    data['Тендер №'] = tender_number

    # полуение названия
    name = soup.find('h1', class_='tender-header__h4').text.strip()
    data['Название тендера'] = name

    # получение начальной цены
    price = soup.find('span', class_='tender-body__text').text.strip()
    data['Начальная цена'] = price

    # получение даты окончания
    date = soup.find('span', class_='black').text.strip()
    data['Дата окончания'] = date

    # получение места поставки
    place = soup.find(
        'div',
        attrs={'data-id': 'place'},
        class_='line-clamp line-clamp--n5'
    )
    cleaned_place = ' '.join([text.strip() for text in place.strings if text.strip()])
    data['Место поставки'] = cleaned_place

    return data


def main(max_count, output_file):
    print(f"Парсим максимум {max_count} тендеров.")
    print(f"Сохраняем в файл: {output_file}")

    print('Вход в аккаунт')
    if login():

        all_links = get_links(max_count)

        all_data = []
        for idx, link in enumerate(all_links, start=1):
            print(f'[{idx}] Парсинг {link}')
            sub_html = get_html(link)
            if sub_html:
                data = parse_data(sub_html)
                data['Ссылка'] = link
                print(f'[{idx}] Парсинг завершен')
                all_data.append(data)
            time.sleep(0.5)

        # сохраняем результат
        print('Сохраняю данные в файл...')
        df = pd.DataFrame(all_data)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print('Bye!')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Парсер тендеров")
    parser.add_argument('--max', type=int, default=30, help='Максимальное количество тендеров для парсинга')
    parser.add_argument('--output', type=str, default='tenders.csv', help='Имя файла для сохранения результата')

    args = parser.parse_args()
    main(args.max, args.output)

