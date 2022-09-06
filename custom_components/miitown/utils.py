import time
from typing import Union


class AuthError(Exception):
    pass


def handle_response(response: Union[dict, list]) -> None:
    code = str(response.get("code"))
    if type(response) == list or code == "200":
        return
    elif code == "-401" or code == "-404":
        raise AuthError("Token is invalid")
    raise Exception(response["message" if response.get("message") else "msg"])


def battery_parse(value: int) -> int:
    max_val = 410
    min_val = 340
    if value < max_val:
        value = 0 if value < min_val else 100 * (value - min_val) / (max_val - 5 - min_val)

    return 100 if value > 100 else int(value)


def clone_dict_list(old_list: list[dict]) -> list[dict]:
    new_list = []
    for item in old_list:
        new_list.append(item.copy())

    return new_list


def format_devices(devices: list[dict], device_metas: list[dict]):
    new_devices = []
    for device in clone_dict_list(devices):
        for meta in device_metas:
            should_break = False
            device["isConnected"] = False
            device["isLowPower"] = False
            device["battery"] = 0
            time_now = int(time.time())
            if meta.get("conn") is not None and (
                    meta["conn"]["imei"] == device["imei"] or meta["conn"]["imei"] == device["serialNumber"]):
                should_break = True
                if time_now - meta["conn"]["connTime"] <= 900:
                    device["isConnected"] = True
                device["lastSeen"] = meta["conn"]["connTime"]

            if meta.get("position") is not None and (
                    meta["position"]["imei"] == device["imei"] or meta["position"]["imei"] == device["serialNumber"]):
                should_break = True
                device["gpsTime"] = meta["position"]["gpsTime"]
                device["height"] = meta["position"]["high"]
                device["latitude"] = meta["position"]["lat"]
                device["longitude"] = meta["position"]["lng"]
                device["satellites"] = meta["position"]["sates"]
                device["speed"] = meta["position"]["speed"]
                device["upMode"] = meta["position"]["upMode"]
                if time_now - meta["position"]["gpsTime"] <= 60 and meta["position"]["speed"] > 3:
                    device["isDriving"] = True
                else:
                    device["isDriving"] = False

            if meta.get("power") is not None and (
                    meta["power"]["imei"] == device["imei"] or meta["power"]["imei"] == device["serialNumber"]):
                should_break = True
                device["isLowPower"] = False
                if meta["power"]["po"] != 1:
                    device["battery"] = battery_parse(meta["power"]["inside"])
                    if device["battery"] <= 20:
                        device["isLowPower"] = True
                else:
                    device["battery"] = 100

            if should_break:
                new_devices.append(device)
                break

    return new_devices
