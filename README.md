# ipq807 Openwrt Sysupgrade Server

A simple Sysupgrade-like server that will allow rapid access to [robimarko's firmwares](https://github.com/robimarko/openwrt) by proxying requests to github and creating a sysupgrade standard response.

#
## How to make it work

### The easy way
I have already configured a public server, reachable via:
https://sysupgrade.eleet.dev/

To use it directly just proceed as follows:

- Navigate to System->Attended Sysupgrade
- Select the "Configuration" tab
- Under "Server -> Address" insert one of the following links (choose your device):
    - https://sysupgrade.eleet.dev/dynalink_dl
    - https://sysupgrade.eleet.dev/edgecore_eap102
    - https://sysupgrade.eleet.dev/edimax_cax1800
    - https://sysupgrade.eleet.dev/qnap_301w
    - https://sysupgrade.eleet.dev/redmi_ax6
    - https://sysupgrade.eleet.dev/xiaomi_ax3600
    - https://sysupgrade.eleet.dev/xiaomi_ax9000

If a new ipq807 device will be added to the builds it will automatically appear as supported device on this software too.

The updated list can be retrieved in real-time here: https://sysupgrade.eleet.dev/

#
### The "I don't trust you Shoto" way
- install the system requirements: `git` and `py3-pip`
- `git clone https://github.com/ShotokanZH/ipq807x_openwrt_sysupgrade_server.git`
- `cd ipq807x_openwrt_sysupgrade_server`
- `cp config.json.example config.json`
- add your github token to config.json
- `python3 -m pip install -r requirements.txt`
- `python3 -BO sysupgrade.py`
- check for further instructions of your router, opening in the browser: `http://IP_ADDRESS:5000`
