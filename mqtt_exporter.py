#!/usr/bin/env python3

"""
simple metrics exporter from mqtt
"""

import json
import logging
import argparse

from prometheus_client import start_http_server, Enum
import paho.mqtt.client as mqtt


class ArgumentParserReadFileAction(argparse.Action):
    """
    read value from file
    """

    def __call__(self, _parser, namespace, values, _option_string=None):
        if not isinstance(values, str):
            raise argparse.ArgumentError(self, "value must be a sring")
        with open(values, "r", encoding="utf-8") as f:
            setattr(namespace, self.dest, f.readline().strip())


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler()],
)


logger = logging.getLogger(__name__)

aqara_leakage_1_state = Enum(
    "aqara_leakage_1_state",
    "Sensor state",
    states=["water", "dry", "unknown", "not_seen"],
)
aqara_leakage_2_state = Enum(
    "aqara_leakage_2_state",
    "Sensor state",
    states=["water", "dry", "unknown", "not_seen"],
)


def on_connect(client, _userdata, _flags, rc):
    """
    mqtt connection handler
    """
    if rc == 0:
        logger.debug("subscribe")
        client.subscribe("zigbee2mqtt/Aqara leakage sensor 1/#")
        client.subscribe("zigbee2mqtt/Aqara leakage sensor 2/#")
        # client.subscribe("zigbee2mqtt/#")
    else:
        logger.error("on_connect status %s", rc)


def on_message(_client, _userdata, message):
    """
    mqtt message handler
    """
    try:
        if message.topic == "zigbee2mqtt/Aqara leakage sensor 1":
            aqara_leakage_1_state.state(read_aqara_leakage_state(message))
        elif message.topic == "zigbee2mqtt/Aqara leakage sensor 2":
            aqara_leakage_2_state.state(read_aqara_leakage_state(message))
        else:
            pass
    except ValueError as e:
        logger.error("error on_message %s", e)


def read_aqara_leakage_state(message):
    """
    reads field water_leak from sensor content
    """
    try:
        logger.debug("read_aqara_leakage_state")
        json_data = json.loads(message.payload.decode())
        val = json_data.get("water_leak")
        if val is None:
            return "unknown"
        if val is True:
            return "water"
        return "dry"
    except json.JSONDecodeError as e:
        logger.error("decode error %s", e)
        return "unknown"


def mqtt_loop(broker, user, password):
    """
    setup mqtt-client and loop forever
    """
    client = mqtt.Client()
    client.username_pw_set(user, password)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker, 1883, 0)
    client.loop_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="mqtt_exporter",
        description="reads data from the mqtt server and publishes it as prometheus metrics",
    )
    parser.add_argument(
        "-b", required=True, dest="mqtt_broker", help="broker name or address"
    )
    parser.add_argument("-u", required=True, dest="mqtt_user", help="username")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-p", dest="passwd", help="password")
    group.add_argument(
        "-pf",
        dest="passwd",
        action=ArgumentParserReadFileAction,
        help="path to file that stores a password",
    )

    args = parser.parse_args()

    print(args)

    start_http_server(8000)
    aqara_leakage_2_state.state("not_seen")
    aqara_leakage_2_state.state("not_seen")
    while True:
        mqtt_loop(args.mqtt_broker, args.mqtt_user, args.passwd)
