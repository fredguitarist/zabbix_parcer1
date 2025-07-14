import requests
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ZABBIX_URL = 'https://zabbix.nonton.tech/api_jsonrpc.php'
ZABBIX_USER = 'Admin'
ZABBIX_PASSWORD = *

def zabbix_api(method, params, auth_token=None):
    headers = {'Content-Type': 'application/json-rpc'}
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
        "auth": auth_token
    }
    response = requests.post(ZABBIX_URL, headers=headers, json=payload, verify=False)
    res = response.json()
    if 'error' in res:
        print("Ошибка от Zabbix API:", res['error'])
        exit(1)
    return res['result']

def get_average_utilization(auth, hostid, key):
    items = zabbix_api('item.get', {
        "hostids": hostid,
        "search": {"key_": key},
        "output": ["itemid"]
    }, auth)
    
    if not items:
        return None
    
    itemid = items[0]['itemid']
    
    now = int(time.time())
    month_ago = now - 30*24*60*60
    
    history = zabbix_api('history.get', {
        "history": 0,
        "itemids": itemid,
        "time_from": month_ago,
        "time_till": now,
        "output": "extend",
        "sortfield": "clock",
        "sortorder": "ASC",
        "limit": 10000
    }, auth)
    
    if not history:
        return None
    
    values = [float(entry['value']) for entry in history]
    return sum(values) / len(values)

def main():
    auth = zabbix_api('user.login', {
        "username": ZABBIX_USER,
        "password": ZABBIX_PASSWORD
    })

    hosts = zabbix_api('host.get', {
        "output": ["hostid", "name"],
        "selectInterfaces": ["ip"]
    }, auth)

    print(f"{'Хост':<30}\t{'IP':<15}\t{'Средняя утилизация памяти (%)':<28}\t{'Средняя утилизация CPU (%)':<27}\t{'Средняя утилизация диска (%)':<28}")

    for host in hosts:
        hostid = host['hostid']
        hostname = host['name']
        interfaces = host.get("interfaces", [])
        ip = interfaces[0].get("ip", "N/A") if interfaces else "N/A"

        avg_mem = get_average_utilization(auth, hostid, "vm.memory.utilization")
        avg_cpu = get_average_utilization(auth, hostid, "system.cpu.util")
        avg_disk = get_average_utilization(auth, hostid, "vfs.dev.util[vda]")

        mem_str = f"{avg_mem:.2f}%" if avg_mem is not None else "Нет данных"
        cpu_str = f"{avg_cpu:.2f}%" if avg_cpu is not None else "Нет данных"
        disk_str = f"{avg_disk:.2f}%" if avg_disk is not None else "Нет данных"

        print(f"{hostname:<30}\t{ip:<15}\t{mem_str:<28}\t{cpu_str:<27}\t{disk_str:<28}")

    zabbix_api('user.logout', {}, auth)

if __name__ == '__main__':
    main()
