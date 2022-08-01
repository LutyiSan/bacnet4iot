from loguru import logger
from csv_to_dict import get_device_dict
from BACnet import BACnetClient
from mqtt import MyMQTT
from tsdb import TSDB
from env import *


class GTW:

    def __init__(self):
        self.ts = TSDB()

    def create_mqtt(self):
        self.mqttclient = MyMQTT()
        self.mqttclient.create(USER_NAME, USE_PASSWD)

    def run_bacnet(self):
        self.bacnet = BACnetClient()
        for i in DEVICE_CSV:
            state = self.bacnet.create(HOST_IP, HOST_PORT)
            if state:
                #  Получаем словарь из csv девайса
                self.device = get_device_dict(i)
                if self.device:
                    if TSDB_ENABLE:
                        #  Создаем таблицу девайса в БД
                        self.ts.create_table(f'{self.device["TOPIC"][1]}')
                        # Опрашиваем девайс
                    self.reading_data = self.bacnet.read_load(self.device)
                    self.bacnet.disconnect()
                    self.sent_data()
                    if TSDB_ENABLE:
                        # Сохраняем полученые данные в БД
                        self.ts.put_data(f'{self.device["TOPIC"][1]}', self.reading_data)
                    # Отправляем полученые данные в MQTT

                else:
                    logger.info(f"FAIL read csv {i}")

            else:
                logger.info("Please inspect parameters in env.py")
                # return False

    def sent_data(self):
        sent_data = dict.fromkeys(self.reading_data['OBJECT_NAME'])
        idx = -1
        for i in sent_data:
            idx += 1
            sent_data[i] = self.reading_data['PRESENT_VALUE'][idx]
        if self.mqttclient.connect(BROKER, BROKER_PORT):
            self.mqttclient.send(f'{TOPIC}/{self.device["TOPIC"][1]}', sent_data)


def run():
    gtw = GTW()
    gtw.create_mqtt()
    while True:
        gtw.run_bacnet()
        # if not bcc_state:
        # break


if __name__ == '__main__':
    run()

