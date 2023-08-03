import time
from pathlib import Path
import argparse

# import click
# from dbus.mainloop.glib import DBusGMainLoop
import yaml
from mpris2 import get_players_uri

# from globals import logger
from lastfm_mpris2_scrobbler.Scrobbler import Scrobbler


# @click.command()
# @click.argument("config_file")
# def main(config_file):
def main():
    # dbus_loop = DBusGMainLoop(set_as_default=True)
    parser = argparse.ArgumentParser(
        prog='lastfm-mpris2-scrobbler',
        description='Last.fm scrobbler for Linux'
    )
    parser.add_argument("-c", "--config", dest="config_file", help='config.yaml file path')
    parser.add_argument("--list-players", action="store_true", help="list all active MPRIS2 media players")
    args = parser.parse_args()

    if args.list_players:
        print("---List of active MPRIS2 media players---")
        for p in get_players_uri():
            print(p)
        return

    # load config
    if Path(args.config_file).is_file():
        with open(args.config_file, "r") as file:
            config = yaml.safe_load(file)
    else:
        raise FileNotFoundError("The specified config file " + args.config_file + " cannot be found")

    scrobbler = Scrobbler(**config)

    while True:
        try: 
            scrobbler.connect_to_all_players()
            scrobbler.scrobble_all_players()
        except Exception as e:
            pass
        time.sleep(5)

if __name__ == "__main__":
    main()
