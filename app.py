import streamlit as st
from streamlit_option_menu import option_menu
from stvis import pv_static
from validators import url
from time import sleep
import pyvis
import script

st.set_page_config(layout="wide")
title_start = st.header("Графическая модель структуры веб-ресурса (карта сайта)")

# Инициализация состояния
if "option_menu" not in st.session_state:
    st.session_state["option_menu"] = False
if "option_menu_create" not in st.session_state:
    st.session_state["option_menu_create"] = False
if "option_menu_save" not in st.session_state:
    st.session_state["option_menu_save"] = False
if "option_menu_upload" not in st.session_state:
    st.session_state["option_menu_upload"] = False
if "option_menu_expand" not in st.session_state:
    st.session_state["option_menu_expand"] = False

if "file" not in st.session_state:
    st.session_state["file"] = ""

if "create_clicked" not in st.session_state:
    st.session_state["create_clicked"] = False

if "line" not in st.session_state:
    st.session_state["line"] = []
if "network_base" not in st.session_state:
    st.session_state["network_base"] = []
if "network" not in st.session_state:
    st.session_state["network"] = False

if "button_start" not in st.session_state:
    st.session_state["button_start"] = False

def create_callback():
    # Нажата кнопка создания модели
    st.session_state["create_clicked"] = True


def callback_file():
    # Нажата кнопка создания модели
    st.session_state["create_clicked"] = True


if "address" not in st.session_state:
    st.session_state["address"] = ""
if "mode" not in st.session_state:
    st.session_state["mode"] = 1
if "form_shown" not in st.session_state:
    st.session_state["form_shown"] = False
if "validation_passed" not in st.session_state:
    st.session_state["validation_passed"] = False

navigation_menu = option_menu(
    menu_title="Функции для работы с моделями:",
    options=["Создать модель", "Сохранить модель", "Загрузить модель", "Расширить модель"],
    icons=['patch-plus', 'download', "upload", 'node-plus'],
    menu_icon="cast",
    orientation="horizontal",
    key="option_menu"
)





# Создание модели

def start():
    st.session_state["stage"] = "stop"
def stop():
    st.session_state["stage"] = "finale"
if "stage" not in st.session_state:
    st.session_state["stage"] = "start"

if st.session_state["option_menu"] == "Создать модель":
    # Форма для ввода данных
    with st.form(key="creation"):
        start_address = st.text_input(label="Введите URI-адрес веб-страницы (сайта), с которого хотели бы начать:",
                                      value=st.session_state["address"])
        mode = st.radio("Выберите режим работы:", ("Ручной (Для расширения карты потребуется ваш выбор)",
                                                   "Потоковый (Карта будет создаваться автоматизировано пока не достигнет глубины в 3 ссылки)"),
                        index=st.session_state["mode"] - 1)
        button_start = st.form_submit_button("Начать генерацию", on_click=start)

    # Обработка данных формы
    if button_start:
        st.session_state["button_start"] = True
        st.session_state["address"] = start_address.strip()
        st.session_state["mode"] = 1 if mode == "Ручной (Для расширения карты потребуется ваш выбор)" else 2

        # Валидация адреса
        if url(st.session_state["address"]):
            st.success("Адрес верен, приступаем к созданию карты")
            st.session_state["validation_passed"] = True  # Адрес прошел валидацию
            st.session_state["option_menu_create"] = True
            sleep(2)

            with st.form(key="handle"):
                button_stop = st.form_submit_button("Остановить сбор данных", on_click=stop)
                #st.session_state["button_stop"] = False

                if st.session_state["mode"] == 1:
                    line = [[0, st.session_state["address"]]]  # Конвеерная лента для страниц
                    network_base = [dict(), dict()]
                    # MAX_LEVEL = 1  # Масимальная глубина поиска
                    numbers = st.empty()
                    while (line != []):
                        line, network_base = script.do_scrap_handly(*line[0], line, network_base)
                        with numbers.container():
                            status = st.write(f"На данный момент: Всего ссылок найдено - {len(line)+len(network_base[0])}; Ссылок обработано - {len(network_base[0])}.")
                        st.session_state['line'], st.session_state['network_base'] = line, network_base
                    stop()
                    #st.write(f"Итого:\n Всего ссылок найдено - {len(line)}\n Ссылок обработано - {len(network_base[0])}")

                elif st.session_state["mode"] == 2:
                    line = [[0, st.session_state["address"]]]  # Конвеерная лента для страниц
                    network_base = [dict(), dict()]
                    # MAX_LEVEL = 3  # Масимальная глубина поиска
                    numbers = st.empty()
                    while (line != []):
                        line, network_base = script.do_scrap_auto(*line[0], line, network_base)
                        with numbers.container():
                            status = st.write(f"На данный момент: Всего ссылок найдено - {len(line)+len(network_base[0])}; Ссылок обработано - {len(network_base[0])}.")
                        st.session_state['line'], st.session_state['network_base'] = line, network_base
                    stop()

        else:
            st.error("Адрес, который вы ввели, не является верным. Пожалуйста, попробуйте ввести другой адрес")
            st.session_state["validation_passed"] = False  # Адрес не прошел валидацию

    if st.session_state["stage"] == "finale":
        status = st.write(f"Итого: Всего ссылок найдено - {len(st.session_state['line'])+len(st.session_state['network_base'][0])}; Ссылок обработано - {len(st.session_state['network_base'][0])}.")
        network = script.make_graph(st.session_state["network_base"])
        st.session_state["network"] = network
        st.success("Модель успешно создана")
        st.session_state["stage"] = "start"

    if st.session_state["network"]:
        pv_static(st.session_state["network"])





# Сохранение модели # DONE НО ТУТ ТРАБЛЫ С РЕДИРЕКТАМИ ПРИ ПАРСИНГЕ

def save(network_base):
    file = ""
    for k, m in network_base[0].items():
        file += (k + " ||| " + "|||".join(m) + '\n')
    file += ("+++++++++++++++++++++++++\n")
    for k, m in network_base[1].items():
        file += (k + " ||| " + m + '\n')
    return file


if st.session_state["option_menu"] == "Сохранить модель":
    if (st.session_state["option_menu_upload"] or st.session_state["option_menu_create"]) and st.session_state[
        "network_base"]:
        datasave = "Нет данных"
        if st.session_state["network_base"]:
            datasave = st.session_state["network_base"]
        st.download_button("Сохранить модель как txt-файл",
                           data=save(datasave),
                           file_name="model.txt",
                           mime="text")
        if st.session_state["network"]:
            pv_static(st.session_state["network"])
    else:
        st.error("Нет модели для сохранения. Для создания модели перейдете в раздел \"Создать модель\"")





# Загрузка модели # DONE

def rebuild(ft, deco):
    network_base_upload = [dict(), dict()]
    if ("+++++++++++++++++++++++++" in ft) and (" ||| " in ft):
        while ft[0:25] != "+++++++++++++++++++++++++":
            URI = ft[:ft.find(' ||| ')]
            ft = ft[ft.find(' ||| ') + 5:]
            page_description, logo = ft[:ft.find('|||')], ft[ft.find('|||') + 3:][:ft[ft.find('|||') + 3:].find('\n')]
            ft = ft[ft.find('|||') + 3:]
            ft = ft[ft.find('\n') + 1:]
            network_base_upload[0][URI] = [page_description, logo]
        if deco == 'windows-1251':
            ft = ft[27:]
            while ft != "":
                child_edge = ft[:ft.find(' ||| ')]
                parent_edge = ft[ft.find(' ||| ') + 5:ft.find('\n') - 1]
                ft = ft[ft.find('\n') + 1:]
                network_base_upload[1][child_edge] = parent_edge
            return network_base_upload
        elif deco == 'UTF-8':
            ft = ft[26:]
            while ft != "":
                child_edge = ft[:ft.find(' ||| ')]
                parent_edge = ft[ft.find(' ||| ') + 5:ft.find('\n')]
                ft = ft[ft.find('\n') + 1:]
                network_base_upload[1][child_edge] = parent_edge
            return network_base_upload
    else:
        return None


if st.session_state["option_menu"] == "Загрузить модель":
    # Форма для ввода данных
    uploaded_file = st.file_uploader("Загрузить txt-файл",
                                     type=['txt'],
                                     accept_multiple_files=False)

    if uploaded_file is not None:
        try:
            content = uploaded_file.getvalue().decode('windows-1251')
            decoder = 'windows-1251'
        except:
            content = uploaded_file.getvalue().decode('UTF-8')
            decoder = 'UTF-8'
        with st.form(key="uploadation"):
            button_upload = st.form_submit_button("Создать модель из файла")

        if button_upload:
            if rebuild(content, decoder) is not None:
                st.session_state["network"] = False
                st.success("Файл подходит для создания модели, приступаем к созданию карты")
                st.session_state["option_menu_upload"] = True  # Файл прошел валидацию
                st.session_state["network_base"] = rebuild(content, decoder)
                sleep(2)
                # st.write(st.session_state["network_base"])

                network = script.make_graph(st.session_state["network_base"])
                st.session_state["network"] = network
                st.success("Модель успешно создана")

            else:
                st.error("Файл не подходит для генерации модели. Загрузите другой файл")
                st.session_state["option_menu_upload"] = False  # Файл не прошел валидацию

    if st.session_state["network"]:
        pv_static(st.session_state["network"])





# Расширение модели

if "expand_address" not in st.session_state:
    st.session_state["expand_address"] = ""
if "not_expanded" not in st.session_state:
    st.session_state["not_expanded"] = False

def get_not_expanded(net):
    not_expanded = []

    for link in net.get_nodes():
        if link not in (row["from"] for row in net.get_edges()):
            not_expanded.append(link)

    return not_expanded

if st.session_state["option_menu"] == "Расширить модель":
    if (st.session_state["option_menu_expand"] or st.session_state["option_menu_create"] or st.session_state["option_menu_upload"]) and st.session_state["network_base"]:

        st.session_state["not_expanded"] = get_not_expanded(st.session_state["network"])

        with st.form(key="uploadation"):
            st.session_state["expand_address"] = st.selectbox("Выберите узел модели для расширения:", st.session_state["not_expanded"])
            button_expand = st.form_submit_button("Расширить модель", on_click=start)

        if button_expand:

            with st.form(key="handle"):
                button_stop = st.form_submit_button("Остановить расширение модели", on_click=stop)
                #st.session_state["button_stop"] = False
                line = [[0, st.session_state["expand_address"]]]  # Конвеерная лента для страниц
                network_base = st.session_state["network_base"]
                # MAX_LEVEL = 1  # Масимальная глубина поиска
                numbers = st.empty()
                while (line != []):
                    line, network_base = script.do_scrap_handly(*line[0], line, network_base)
                    with numbers.container():
                        status = st.write(f"На данный момент: Всего ссылок найдено - {len(line) + len(network_base[0])}; Ссылок обработано - {len(network_base[0])}.")
                    st.session_state['line'], st.session_state['network_base'] = line, network_base
                stop()

    else:
        st.error("Нет модели для расширения. Для создания модели перейдете в раздел \"Создать модель\"")

    if st.session_state["stage"] == "finale":
        status = st.write(f"Итого: Всего ссылок найдено - {len(st.session_state['line'])+len(st.session_state['network_base'][0])}; Ссылок обработано - {len(st.session_state['network_base'][0])}.")
        network = script.make_graph(st.session_state["network_base"])
        st.session_state["network"] = network
        st.success("Модель успешно расширена")
        st.session_state["stage"] = "start"

    if st.session_state["network"]:
        pv_static(st.session_state["network"])

#st.write(st.session_state)

