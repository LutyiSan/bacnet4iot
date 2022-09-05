from loguru import logger
from csv_to_dict import csv_to_dict
from BACnet import BACnetClient
from mqtt import MyMQTT
import multiprocessing
from env import *


def time_control(period, func):
    run_time = multiprocessing.Process(target=func)
    run_time.start()
    # Wait for 10 seconds or until process finishes
    run_time.join(period)
    # If thread is still active
    if run_time.is_alive():
        # print("running... before changed values...")
        # Terminate - may not work if process is stuck for good
        run_time.terminate()
        # OR Kill - will work for sure, no chance for process to finish nicely however
        # p.kill()
        run_time.join()


class GTW:

    def run_bacnet(self):
        self.bacnet = BACnetClient()
        for device in DEVICE_CSV:
            self.device = csv_to_dict(device, ';')  # Получаем словарь из csv девайса
            if self.device:
                time_control(5, self.bacnet.create(HOST_IP, self.device['PORT'][0]))
                # Опрашиваем девайс
                if MILTIREAD_LENGTH > 1:
                    self.reading_data = self.bacnet.read_load(self.device)
                    self.bacnet.disconnect()
                else:
                    self.reading_data = self.bacnet.read_single(self.device)
                    self.bacnet.disconnect()
                self.mqttclient = MyMQTT()
                self.mqtt_create_state = self.mqttclient.create(USER_NAME, USE_PASSWD)
                if self.mqtt_create_state:
                    self.sent_data()
                else:
                    logger.error(f"MQTT Client not created")
            else:
                logger.info(f"FAIL read csv {device}")
           #     self.bacnet.disconnect()

    def sent_data(self):
        sent_data = dict.fromkeys(self.reading_data['OBJECT_NAME'])
        idx = -1
        for i in sent_data:
            idx += 1
            sfs = GTW.sign_sf(self.reading_data['STATUS_FLAGS'][idx])
            sent_data[i] = [self.reading_data['PRESENT_VALUE'][idx], sfs]
        for v in sent_data:
            logger.info(f"Send to MQTT {v} -  present-value: {sent_data[v][0]} status-flags: {sent_data[v][1]} ")
        if self.mqttclient.connect(BROKER, BROKER_PORT):
            self.mqttclient.send(f'{TOPIC}/{self.device["TOPIC"][1]}', sent_data)

    @staticmethod
    def sign_sf(sf):
        if len(sf) == 4:
            if sf[0]:
                sf[0] = 'in-alarm'
            if sf[1]:
                sf[1] = 'fault'
            if sf[2]:
                sf[2] = 'overridden'
            if sf[3]:
                sf[3] = 'is-not-service'
            return sf
        else:
            return ['Null', 'Null', 'Null', 'Null']


def run():
    gtw = GTW()
    while True:
        gtw.run_bacnet()


if __name__ == '__main__':
    run()
