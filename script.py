# Создание запросов
import requests
# Парсинг
from bs4 import BeautifulSoup
from bs4.dammit import EncodingDetector
# Валидатор URI-адреса
from validators import url
# Сбор ключевых фраз
import yake
# Генерация графической модели
import pyvis

import streamlit as st


# Просто небольшая стандартизация адреса, убираем последений символ если это /
def clean_end_URI(URI):
    if URI[-1] == '/':
        URI = URI[:-1]
    return URI


# Забавно, но добавляет / в конец адреса, если только этот адрес оканчивается на имя директории
def get_standart_URI(URI):
    URI = URI.strip()
    URI = clean_end_URI(URI)
    copy = URI

    part1 = URI[:URI.find('//') + 2]
    part2 = URI[URI.find('//') + 2:]
    if part2.find('/') != -1:
        part2 = part2[:part2.find('/')]
    root = part1 + part2

    URI = URI.replace(root, '')

    last = URI[URI.rfind('/') + 1:]
    if last == '':
        stand = root + '/'
    elif '.' not in last:
        stand = copy + '/'
    else:
        stand = copy
    return stand


# Проверка по правилу: веб-страница обязательно html или php или директория
def true_web_file(URI, flag=False):
    no_protocol = URI[URI.find('//') + 2:]
    if no_protocol.find('/') != -1:
        rest = no_protocol[no_protocol.find('/') + 1:]
    else:
        flag = True
        return flag

    last = rest[rest.rfind('/') + 1:]

    if last.rfind('.') == -1:
        flag = True
    elif last[last.rfind('.') + 1:] == '':
        flag = True
    elif last[last.rfind('.') + 1:] not in ("exe", "bat", "msi", "dll", "sh", "dmg"): # 'html' in last[last.rfind('.') + 1:] or 'php' in last[last.rfind('.') + 1:]
        flag = True
    return flag


# Парсим заголовок страницы как часть её описания в модели
def get_title(soup, URI):
    try:
        if soup.title == None:
            result = URI
        else:
            result = soup.title.text
            if result is None:
                result = soup.title.string
        return result
    except:
        if url(URI):
            return URI
        else:
            return "Неизветсная страница"


# Получаем список ключевых слов с помощью yake
def get_plot(soup):
    if isinstance(soup, str):
        text = soup
    else:
        text = soup.text
    text = text.replace("\n", " ")

    kw_extractor = yake.KeywordExtractor(lan='ru', n=7, dedupLim=0.3, windowsSize=1, top=10)
    keywords = kw_extractor.extract_keywords(text)

    plot = "\nСписок ключевых слов:\n"
    for i in range(len(keywords)):
        plot += f"{i + 1}. {keywords[i][0]}\n"

    return plot


# Ищем на странице мета-тэги с описанием и ключевыми словами
def get_meta(soup):
    try:
        description = soup.find_all(
            lambda tag: tag.name == 'meta' and tag.has_attr("name") and tag["name"] == "description", limit=1)
        description = description[0]["content"]
    except:
        description = ''
    try:
        keywords = soup.find_all(lambda tag: tag.name == 'meta' and tag.has_attr("name") and tag["name"] == "keywords",
                                 limit=1)
        keywords = keywords[0]["content"]
    except:
        keywords = ''

    if description != '':
        if keywords != '':
            finale = f"\n\nОписание:\n{description}\nКлючевые слова:\n{keywords}\n"
        else:
            finale = f"\n\nОписание:\n{description}\n"
    elif keywords != '':
        finale = f"\n\nКлючевые слова:\n{keywords}\n"
    else:
        finale = '\n'

    return finale


# Данная функция находит фавикон и парсит его со страницы. Если фавикон не найден, то возвращает пустой адрес фавикона
def get_logo(soup):
    try:
        icon_link = soup.find_all(lambda tag: tag.name == 'link' and tag.has_attr("rel") and tag["rel"] in (["shortcut", "icon"], ["Shortcut", "Icon"], ["alternate", "icon"], ["icon"]), limit=1)
        if icon_link == []:
            return ''
        elif icon_link[0]["href"][-5:] == "svg?4":
            icon_link = soup.find_all(lambda tag: tag.name == 'link' and tag.has_attr("rel") and tag["rel"] in (["shortcut", "icon"], ["Shortcut", "Icon"], ["alternate", "icon"]), limit=1)
        return icon_link[0]["href"]
    except:
        return ''


# Готовим файл к парсингу. Файлы только из сети Интернет или подобных
def cook_soup(URI):
    URI = get_standart_URI(URI)

    try:
        if not (url(URI)):  # Проверяем валидность как адреса в сети или как места на диске
        # not((':\\' in URI)
        # print("Адрес ведёт не на веб-страницу")
            return URI

        # elif ':\\' in URI:  # Срабатывает если файл локальный
        # with open(URI, encoding="utf8") as file:
        # soup = BeautifulSoup(file, "html.parser")
        # file.close()
        # return soup

        elif url(URI):  # Срабатывает если файл веб
            if true_web_file(URI):
                URI = clean_end_URI(URI)
                headers = {
                    "User-Agent": r"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0"}
                page_text = requests.get(URI, headers=headers, allow_redirects=False)
                http_encoding = page_text.encoding if 'charset' in page_text.headers.get('content-type',
                                                                                        '').lower() else None
                html_encoding = EncodingDetector.find_declared_encoding(page_text.content, is_html=True)
                encoding = html_encoding or http_encoding
                soup = BeautifulSoup(page_text.content, 'html.parser', from_encoding=encoding)

                if get_title(soup, URI) in ("307 Temporary Redirect", "302 Found"):
                    URI = get_standart_URI(URI)
                    headers = {
                        "User-Agent": r"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0"}
                    page_text = requests.get(URI, allow_redirects=True, headers=headers)
                    http_encoding = page_text.encoding if 'charset' in page_text.headers.get('content-type',
                                                                                            '').lower() else None
                    html_encoding = EncodingDetector.find_declared_encoding(page_text.content, is_html=True)
                    encoding = html_encoding or http_encoding
                    soup = BeautifulSoup(page_text.content, 'html.parser', from_encoding=encoding)

                return soup

            else:  # Срабатывает если файл веб, но не html
                return URI

    except Exception as e:  # На всякий пожарный
        #print(f"Что-то совсем пошло не так: {e}\n\n {URI}")
        return None


def check_domain(URI, link, rule=False):
    if url(link):
        if rule:
            domain = clean_end_URI(URI[URI.find('//') + 2:])
            if domain.find('/') != -1:
                domain = domain[:domain.find('/')]
        else:
            return True

        return domain in link

    else:
        return True


# Немножко сложный конструктор ссылок из того барахла в href, что найдены на странице. Спасибо валидатору ссылок.
def build_link(URI: str, URL: str, link: str) -> str:
    # print(link)
    URL = clean_end_URI(URL)
    link = link.strip()

    if link != '' and link != '/':  # done
        if link[-1] == '/':
            link = link[:-1]

    if (url(link) or link[0:7] == 'mailto:'):  # done
        full = link

    elif link == '':  # done
        full = URI
    elif link[0:2] == '//':
        full = "https:" + link
    elif link[0] == '/':  # done
        part1 = URI[:URI.find('//') + 2]
        part2 = URI[URI.find('//') + 2:]
        if part2.find('/') != -1:
            part2 = part2[:part2.find('/')]

        full = part1 + part2 + link

    else:
        flag = link.count('../')
        link = link.replace('../', '')

        if flag != 0:
            for i in range(flag):
                URL = URL[:URL.rfind('/')]
            full = URL + '/' + link
        elif link[0] == "?":
            full = URI + link
        else:
            full = URL + '/' + link

    return full


def build_dir(URI: str) -> str:
    URI = clean_end_URI(URI)
    if ':\\' in URI:
        URL = URI[:URI.rfind("\\")]
    else:
        if URI.rfind("/", URI.find("//") + 2) == -1:
            URL = URI + '/'
        else:
            URL = URI[:URI.rfind("/", URI.find("//") + 2)] + '/'  # вычленяем URL-адрес сайта
    # print(URL)

    return URL


# Выбираем только видимые пользователю ссылки и доделываем их до полного URI-адреса. Ссылки выбираем по атрибуту href
def get_links(URI: str, page: str, parent_domain_flag=False) -> list:
    try:
        hyperlinks = page.find_all(lambda tag: tag.has_attr("href") and tag.name != 'link')
        #print(len(hyperlinks), end=' # ')
        hyperlinks = [x for x in hyperlinks if (((x['href'][0] != "#") and check_domain(URI, x['href'].strip(), rule=parent_domain_flag)) if x['href'] != '' else False)]
        #print(len(hyperlinks), end=' # ')
        hyperlinks = [build_link(URI, build_dir(URI), item['href']) for item in hyperlinks]

        return hyperlinks
    except:
        return []


def do_scrap_auto(level, URI, line, network_base, MAX_LEVEL=3):
    try:
        soup = cook_soup(URI)  # Непосредственно парсинг html-страницы

    except Exception as e:
        pass

    else:
        if soup == None or soup == URI:
            network_base[0][URI] = [URI, '']
            # print(URI)

        else:
            page_title = get_title(soup, URI)  # Парсим тэг title страницы

            network_base[0][URI] = [page_title + get_meta(soup) + get_plot(soup),
                                    build_link(URI, URI, get_logo(soup))]  # Делаем запись в Nodes
            if level < MAX_LEVEL:  # Только если не дошли до последнего уровня

                hyperlinks = get_links(URI, soup)  # Находим на странице ссылки href

                # print(len(hyperlinks), end=' # ')
                hyperlinks = [x for i, x in enumerate(hyperlinks) if (
                            (x not in hyperlinks[:i]) and (x not in (URI, URI + '/')) and (
                                x not in network_base[0].keys()) and (
                            (x not in (row[1] for row in line))))]  # Выбираем уникальные ссылки
                # print(len(hyperlinks))

                for link in hyperlinks:  # Делаем запись в Edges
                    if link not in network_base[1].keys():
                        network_base[1][link] = URI

                # print(*hyperlinks, sep="\n")
                line += zip([level + 1] * len(hyperlinks), hyperlinks)  # Добавляем новые найденные адреса в очередь

    line.pop(0)
    return line, network_base


def do_scrap_handly(level, URI, line, network_base, MAX_LEVEL=1):
    try:
        soup = cook_soup(URI)  # Непосредственно парсинг html-страницы

    except Exception as e:
        pass

    else:
        if level <= MAX_LEVEL:
            if soup == None or soup == URI:
                network_base[0][URI] = [URI, '']
                # print(URI)

            else:
                page_title = get_title(soup, URI)  # Парсим тэг title страницы
                network_base[0][URI] = [page_title + get_meta(soup) + get_plot(soup),
                                        build_link(URI, URI, get_logo(soup))]  # Делаем запись в Nodes
                #if level < MAX_LEVEL:  # Только если не дошли до последнего уровня

                hyperlinks = get_links(URI, soup)  # Находим на странице ссылки href

                # print(len(hyperlinks), end=' # ')
                hyperlinks = [x for i, x in enumerate(hyperlinks) if (
                        (x not in hyperlinks[:i]) and (x not in (URI, URI + '/')) and (
                        x not in network_base[0].keys()) and (
                            (x not in (row[1] for row in line))))]  # Выбираем уникальные ссылки
                # print(len(hyperlinks))

                for link in hyperlinks:  # Делаем запись в Edges
                    if link not in network_base[1].keys():
                        network_base[1][link] = URI

                # print(*hyperlinks, sep="\n")
                line += zip([level + 1] * len(hyperlinks), hyperlinks)  # Добавляем новые найденные адреса в очередь

    line.pop(0)
    return line, network_base


# Функция для создания графа (pyvis)
def make_graph(network_base):
    # Создаём объект граф
    net = pyvis.network.Network(notebook=False, height='900px', width='1400px', select_menu=False, filter_menu=True, directed=True, cdn_resources='remote')

    # Добавляем в объект узлы
    length = len(network_base[0])
    for i in range(length):
        if list(network_base[0].values())[i][1] == list(network_base[0].keys())[i]:
            net.add_node(list(network_base[0].keys())[i], label=list(network_base[0].keys())[i], title=list(network_base[0].values())[i][0], color="rgba(2, 94, 161, 1)")
        elif list(network_base[0].values())[i][1] == '':
            net.add_node(list(network_base[0].keys())[i], label=list(network_base[0].values())[i][0], title=list(network_base[0].keys())[i], color="rgba(80, 80, 80, 1)")
        else:
            main_title = list(network_base[0].values())[i][0][:list(network_base[0].values())[i][0].find('\n', 1)].replace('\n', '').strip()
            if main_title != '':
                main_title += '\n'
            net.add_node(list(network_base[0].keys())[i], label=main_title+list(network_base[0].keys())[i], title=list(network_base[0].values())[i][0], shape='image', image=list(network_base[0].values())[i][1], color="rgba(2, 94, 161, 0.8)")
    #net.add_nodes(list(network_base[0].keys()), label=list(network_base[0].values()), title=list(network_base[0].keys()), color=["rgba(125, 125, 125, 1)"] * len(list(network_base[0].values())))

    # Добавляем в объект связи
    try:
        for key, val in network_base[1].items():
            try:
                net.add_edge(val, key, width=3)
            except:
                pass
    except Exception as e:
        print(e)
#        st.write(point)
#        st.write(list(network_base[1].items())[:indx])
#        network_base[1] = dict(list(network_base[1].items())[:indx])

    # vizualise options
    net.set_options("""
    const options = {
     "nodes": {
        "borderWidth": 3,
        "borderWidthSelected": 6,
        "size": 16
      },
      "font": {
          "size": 14,
          "strokeWidth": 2
        },
      "interaction": {
        "hover": true,
        "multiselect": true,
        "navigationButtons": true,
        "tooltipDelay": 0
      },
      "manipulation": {
        "enabled": true,
        "initiallyActive": true
      },
      "physics": {
        "barnesHut": {
        "gravitationalConstant": -16000
        }
      }
    }
    """
                    )
    # "physics": {
    #  "enabled": false,
    #  "minVelocity": 0.75
    #st.write(net)
    #net.show(f"graph_model.html", notebook=False)
    #net.save_graph(f"graph_model.html")
    return net

