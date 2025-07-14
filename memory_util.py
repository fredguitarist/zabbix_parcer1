import requests
import urllib3
import time
from datetime import datetime, timedelta

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

def get_average_memory_utilization(auth, hostid):
    # Получаем элемент с ключом vm.memory.utilization
    items = zabbix_api('item.get', {
        "hostids": hostid,
        "search": {"key_": "vm.memory.utilization"},
        "output": ["itemid"]
    }, auth)
    
    if not items:
        return None
    
    itemid = items[0]['itemid']
    
    # Время за последний месяц
    now = int(time.time())
    month_ago = now - 30*24*60*60
    
    # Получаем историю (тип 0 = float) за последний месяц
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
    avg = sum(values) / len(values)
    return avg

def main():
    auth = zabbix_api('user.login', {
        "username": ZABBIX_USER,
        "password": ZABBIX_PASSWORD
    })

    hosts = zabbix_api('host.get', {
        "output": ["hostid", "name"],
        "selectInterfaces": ["ip"]
    }, auth)

    print(f"{'Хост':<30}\t{'IP':<15}\tСредняя утилизация памяти за месяц (%)")

    for host in hosts:
        hostid = host['hostid']
        hostname = host['name']
        interfaces = host.get("interfaces", [])
        ip = interfaces[0].get("ip", "N/A") if interfaces else "N/A"

        avg_utilization = get_average_memory_utilization(auth, hostid)
        if avg_utilization is None:
            print(f"{hostname:<30}\t{ip:<15}\tНет данных")
        else:
            print(f"{hostname:<30}\t{ip:<15}\t{avg_utilization:.2f}%")

    zabbix_api('user.logout', {}, auth)

if __name__ == '__main__':
    main()
