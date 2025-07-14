import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ZABBIX_URL = 'https://zabbix.nonton.tech/api_jsonrpc.php'
ZABBIX_USER = 'Admin'
ZABBIX_PASSWORD = ***

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

def main():
    auth = zabbix_api('user.login', {
        "username": ZABBIX_USER,
        "password": ZABBIX_PASSWORD
    })

    hosts = zabbix_api('host.get', {
        "output": ["hostid", "name"],
        "selectInterfaces": ["ip"]
    }, auth)

    print(f"{'Хост':<30}\t{'IP':<15}\tУтилизация памяти (%)")

    for host in hosts:
        hostid = host['hostid']
        hostname = host['name']
        interfaces = host.get("interfaces", [])
        ip = interfaces[0].get("ip", "N/A") if interfaces else "N/A"

        items = zabbix_api('item.get', {
            "hostids": hostid,
            "search": {"key_": "vm.memory.utilization"},
            "output": ["lastvalue"]
        }, auth)

        if not items:
            print(f"{hostname:<30}\t{ip:<15}\tНет данных")
            continue

        try:
            utilization = float(items[0]['lastvalue'])
            print(f"{hostname:<30}\t{ip:<15}\t{utilization:.2f}%")
        except Exception:
            print(f"{hostname:<30}\t{ip:<15}\tОшибка данных")

    zabbix_api('user.logout', {}, auth)

if __name__ == '__main__':
    main()

