# Python ver 3.10

import json
import websocket
from datetime import datetime
import numpy as np
from collections import defaultdict
import asyncio
from threading import Lock
import time
import logging
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.ticker import FuncFormatter

# константы для сокета Binance
STREAM1 = 'ethusdt@aggTrade'
STREAM2 = 'btcusdt@aggTrade'

# символы анализируемых валют
SYMB_ETH = 'ETHUSDT'
SYMB_BTC = 'BTCUSDT'
SYMB_ETH_CL = 'ETHUSDT(CLEAR)'

# размер таймфрейма в секундах
TF = 1  # 1 секунда

# размер анализируемой истории
HISTORY_LENGTH = 3600  # 1 час


class Prices:
    """
    класс для хранения котировок валют
    """
    def __init__(self, symbol: str, max_len: int):
        """
        :param symbol: символ валюты
        :param max_len: максимальный размер хранимой истории цен
        """
        self.symbol: str = symbol
        self.prices: list[float] = []  # список цен
        self.time: list[datetime] = []  # список времени цен
        self.len = 0 # текущая длина списков
        self.__max_len = max_len

    @property
    def min(self) -> float:
        """
        :return: минимальная цена за всю хранимую историю
        """
        return min(self.prices) if self.len else 0

    @property
    def max(self) -> float:
        """
        :return: максимальная цена за всю хранимую историю
        """
        return max(self.prices) if self.len else 0

    def append(self, price: float, ticktime: datetime):
        """
        метод добавляет в историю цену
        :param price: добавляемая цена
        :param ticktime: время цены
        :return:
        """
        if self.len == self.__max_len:
            self.prices.pop(0)
            self.time.pop(0)

        self.prices.append(price)
        self.time.append(ticktime)
        self.len += 1


# все цены продаж, произошедших за таймфрейм
last_prices_lock = Lock()
last_prices = defaultdict(list)

# класс хранения данных BTCUSDT
btc_lock = Lock()
btc = Prices(symbol=SYMB_BTC, max_len=HISTORY_LENGTH)
# класс хранения скорректированных данных ETHUSDT
eth_clear_lock = Lock()
eth_clear = Prices(symbol=SYMB_ETH_CL, max_len=HISTORY_LENGTH)
# класс хранения данных ETHUSDT
eth_lock = Lock()
eth = Prices(symbol=SYMB_ETH, max_len=HISTORY_LENGTH)


def pearsons_correlation(x1: np.array, x2: np.array, text: bool = 'True'):
    """
    Функция рассчитывает коэффициент корреляции Пирсона, для определения зависимости векторов двнных
    ! Недостаток 1 - анализируется вся история длиной HISTORY_LENGTH, т.е. если именно в текущий момент движение цены
                     BTC не влияет на ETH, функция это не учтёт, будет возвращён результат влияния за всю историю
    ! Недостаток 2 - чем больше накопившаяся история, тем точнее коэффициент корреляции и эффективнее коррекция, т.к.
                     программа начинает с нулевой истории, поначалу коррекция недостаточно эффективная
    :param x1: первый вектор значений
    :param x2: второй вектор значений
    :param text: вернуть текстовый результат или числовой
    :return: коэффициент корреляции
    """
    pearsons_correlation_result = '' if text else 0
    try:
        len_x1, len_x2 = len(x1), len(x2)
        # из-за асинхронного обращения к данным, возможна ситуация, когда векторы разной длинны,
        # в таком случае последнее значение большего вектора не учитывается
        if len_x1 != len_x2:
            len_x1 = len_x2 = min(len_x1, len_x2)
        if len_x1:  # в самом начале работы программы одного из векторов может ещё не быть
            pearsons_correlation_result = f"Pearson's correlation\n{np.corrcoef(x1[:len_x1], x2[:len_x1])[0, 1]}" if text \
                    else np.corrcoef(x1[:len_x1], x2[:len_x1])[0, 1]
    except Exception as ex:
        print(f'При расчёте коэффициента корреляции возникла ошибка: {logging.exception(ex)}')

    return pearsons_correlation_result


def normalize(x: np.array) -> np.array:
    """
    Функция нормализует график. Среднее значение графика приблизительно становится равным 0,
    движения оотносительно оси x нормализуются
    :param x:  массив цен
    :return: нормализованный массив цен
    """
    normalized_x = np.ones(len(x))
    if(std := x.std()) != 0:
        normalized_x = (x - x.mean()) / std
    return normalized_x


def get_clear_price(main_x: list, influenced_x: list) -> float:
    """
    Функция корректировки цены
    :param main_x: список цен валюты, подлежащей корректировке
    :param influenced_x: список цен валюты, оказывающей влияние
    :return: скорректированное значение последней цены из списка
    """
    clear_price = None
    try:
        std_main = np.std(main_x)  # среднеквадратичное отклонение основного графика
        len_ = min(len(main_x), len(influenced_x))  # выравнивание длин списков
        if len_ and std_main != 0:
            """
            вычисление размера коррекции:
            1. нормализация второго (влияющего) графика
            2. умножение нормализованного графика на среднеквадратичное отклонение первого гафика, т.е.
               приведение его к 'масштабу' первого графика
            3. умножение 'отмасштабированного' графика на коэффициент корреляции (если графики не зависимые,
               тогда корректировка не требуется и коррекция будет равна 0 или близка к 0)
            4. Вычитание из последней цены первого графика величины коррекции
            """
            norm_correction = normalize(np.array(influenced_x)) * std_main * pearsons_correlation(main_x, influenced_x, False)
            clear_price = main_x[-1] - norm_correction[-1]
    except Exception as ex:
        print(f'При корректировке цены возникла ошибка: {logging.exception(ex)}')
    return clear_price


def check_for_extremum(price: float, ticktime, percent):
    """
    Функция проверяет цены на выход за экстремумы
    :param price: цена
    :param ticktime: время цены (для вывода в терминал)
    :param percent: необходимы процент превышения
    :return:
    """
    try:
        if eth_clear.max and (price - eth_clear.max) > eth_clear.max / 100:
            over_percent = (price - eth_clear.max) * 100 / eth_clear.max
            if over_percent > percent:
                print(f"{ticktime} цена {eth_clear.symbol} "
                      f"превысила максимальную за прошедший час на {over_percent}")

        elif eth_clear.min and (eth_clear.min - price) > eth_clear.min / 100:
            under_percent = (eth_clear.min - price) * 100 / eth_clear.min
            if under_percent > percent:
                print(f"{ticktime} цена {eth_clear.symbol} "
                      f"уменьшилась от максимальной за прошедший час на {under_percent}")
    except Exception as ex:
        print(f'При проверке цены на экстремум возникла ошибка: {logging.exception(ex)}')

def write_tf_price(tf:int):
    """
    :param tf: периодичность запуска функции (в секундах)
    :return:
    """
    try:
        # бесконечный цикл
        while True:
            time.sleep(tf)

            # чтение накопившихся за период tf рыночных цен
            # и очистка переменной для записи следующих
            # last_prices - словарь куда поступают данные по ценам с сокета Binance
            with last_prices_lock:
                last_prices_copy = last_prices.copy()
                last_prices.clear()
            # если в списке были цены
            if len(last_prices_copy):
                # получение из списка цены BTCUSDT, высчиление среднего значения за период tf
                # и запись в объект класса Prices
                if prices := last_prices_copy.get(SYMB_BTC):
                    with btc_lock:
                        btc.append(float(np.mean(prices)), datetime.now())
                    # получение из списка цены ETHUSDT, высчиление среднего значения за период tf
                    # и запись в объект класса Prices
                    if prices := last_prices_copy.get(SYMB_ETH):
                        with eth_lock:
                            eth.append(float(np.mean(prices)), datetime.now())
                        # расчёт скорректированной цены ETHUSDT, проверка на экстремум
                        # и запись в объект класса Prices
                        if eth_clear_price := get_clear_price(eth.prices, btc.prices):
                            time_now = datetime.now()
                            check_for_extremum(eth_clear_price, time_now, 1)
                            with eth_clear_lock:
                                eth_clear.append(eth_clear_price, time_now)

    except Exception as ex:
        print(f' При чтении данных возникла ошибка: {logging.exception(ex)}')


def ws_trades():
    """
    Подключение к сокету fstream.binance.com и его прослушивание
    :return:
    """
    socket = f'wss://fstream.binance.com/stream?streams={STREAM1}/{STREAM2}'

    def on_message(wsapp, message):
        json_message = json.loads(message)
        handle_trades(json_message)

    def on_error(wsapp, error):
        print(error)

    wsapp = websocket.WebSocketApp(socket, on_message=on_message, on_error=on_error)
    wsapp.run_forever()


def handle_trades(json_message):
    # при получении цены - запись значения и времени в глобальный словарь
    # для других потоков
    global last_prices
    price = float(json_message['data']['p'])
    with last_prices_lock:
        last_prices[json_message['data']['s']].append(price)


def show_plots():
    """
    Функция отображения графиков.
    :return:
    """
    time.sleep(5)

    formatter = FuncFormatter(lambda y, _: '{:.3f}'.format(y))

    def show_subplot(ax, x_data, y_data, title, text=''):
        ax.clear()
        ax.plot(y_data, x_data)
        ax.set_title(title)
        ax.tick_params(axis='x', labelsize=6, labelrotation=90)
        ax.ticklabel_format(style='plain', axis='y')
        ax.yaxis.set_major_formatter(formatter)
        ax.text(0.1, 0.1, text, horizontalalignment='left', verticalalignment='bottom', transform=ax.transAxes)

    try:
        # Create figure for plotting
        fig = plt.figure(figsize=(12, 9))
        axes = [fig.add_subplot(2, 2, i) for i in range(1, 5)]

        def animate(i):
            # график скорректированных цен ETHUSDT
            if eth_clear.len:  # возможна ситуация в начале работы программы, когда цен ещё нет
                show_subplot(axes[0], eth_clear.prices, eth_clear.time, eth_clear.symbol,
                             pearsons_correlation(eth_clear.prices, btc.prices))
            # график цен BTCUSDT
            if btc.len:
                show_subplot(axes[1], btc.prices, btc.time, btc.symbol,
                             pearsons_correlation(btc.prices, btc.prices))
            # график нормализованных цен BTCUSDT
            normalized_btc = normalize(np.array(btc.prices)).tolist()
            if len(normalized_btc):
                show_subplot(axes[2], normalized_btc, list(range(len(normalized_btc))), btc.symbol +' normalized',
                             pearsons_correlation(normalized_btc, btc.prices))
            # график нескорректированных цен ETHUSDT
            if eth.len:
                show_subplot(axes[3], eth.prices, eth.time, eth.symbol, pearsons_correlation(eth.prices, btc.prices))

        # Set up plot to call animate() function periodically
        anim = animation.FuncAnimation(fig, animate, interval=1000, cache_frame_data=False)

        plt.show()
    except Exception as ex:
        print(f' При выводе графиков произошла ошибка: {logging.exception(ex)}')


async def main():
    try:
        # список сопрограмм - потоков
        tasks = [asyncio.to_thread(ws_trades), asyncio.to_thread(write_tf_price, TF), asyncio.to_thread(show_plots)]
        # запуск всех потоков
        res = await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        [task.close() for task in tasks]
        print("program successfully closed")

asyncio.run(main())
