import network #type: ignore

wlan = network.WLAN(network.STA_IF)

wlan.active(True)

networks = wlan.scan()

# for net in networks:
    # print("SSID: {}, Signal Strength: {}, Encryption: {}".format(net[0].decode('utf-8'), net[3], net[4]))

wlan.connect("C1-101", "12345678")

if (wlan.isconnected()):
    print("Connected to WiFi")
    print("IP Address:", wlan.ifconfig()[0])
    