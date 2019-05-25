from HueBridge import HueBridge


def main():
    bridge = HueBridge()
    bridge.setup()
    bridge.set_light(14, on=True)


main()
