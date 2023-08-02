import time
import click

import datetime
import logging
import coloredlogs
from mpris2 import get_players_uri, Player
import pylast

def get_unix_timestamp():
    return int(time.mktime(datetime.datetime.now().timetuple()))

class PlayerState:
    def __init__(self, metadata_dict, playback_status) -> None:
        self.total_played_time = 0
        self.last_observation_timestamp = get_unix_timestamp()
        self.trackid = ""
        self.if_scrobbled = False
        self.update_status(metadata_dict, playback_status, self.last_observation_timestamp)

    def handle_multiple_artists(self, artist_array):
        # convert artist array into a single string
        return ", ".join(artist_array)
    
    def update_status(self, metadata_dict, playback_status, timestamp):
        # time length of the current song in seconds
        self.length = int(metadata_dict["mpris:length"] / 1000000)
        # image file path
        self.artUrl = str(metadata_dict["mpris:artUrl"])
        self.album = str(metadata_dict["xesam:album"])
        self.albumArtist = self.handle_multiple_artists(metadata_dict["xesam:albumArtist"])
        self.artist = self.handle_multiple_artists(metadata_dict["xesam:artist"])
        self.discNumber = int(metadata_dict["xesam:discNumber"])
        self.firstUsed = str(metadata_dict["xesam:firstUsed"])
        self.title = str(metadata_dict["xesam:title"])
        self.trackNumber = int(metadata_dict["xesam:trackNumber"])
        self.url = str(metadata_dict["xesam:url"])

        # record the timestamp of last observation
        if self.trackid == str(metadata_dict["mpris:trackid"]):
            self.total_played_time += (timestamp - self.last_observation_timestamp) if playback_status == "Playing" else 0
        else:
            self.total_played_time = 0
            self.if_scrobbled = False
        self.trackid = str(metadata_dict["mpris:trackid"])
        self.last_observation_timestamp = timestamp

        # record the playback status in observation
        # May be 'Playing', 'Paused' or 'Stopped'.
        self.playback_status = playback_status

class Scrobbler:
    def __init__(self, **kwargs):
        self.logger = logging.getLogger("dbus-scrobbler")
        coloredlogs.install(level="DEBUG", logger=self.logger)

        self.player_dict = {}

        # TODO: handle network error
        self.network = pylast.LastFMNetwork(
            api_key=kwargs["api_key"],
            api_secret=kwargs["api_secret"],
            username=kwargs["user_name"],
            password_hash=kwargs["password_hash"],
        )
        self.user = self.network.get_user(kwargs["user_name"])
        self.application_whitelist = kwargs["application_whitelist"]

        self.now_playing_tracks_dict = {}
        for app in self.application_whitelist:
            self.now_playing_tracks_dict[app] = ""

        # scrobbler will upload if the track has been played for 4 mins or half the total length
        self.scrobble_time_threshold = 4 * 60

    def connect_to_all_players(self):
        last_observation_uri_list = list(self.player_dict)
        for uri in get_players_uri():
            uri = str(uri)
            if uri in self.application_whitelist:
                p = Player(dbus_interface_info={'dbus_uri': uri})
                if uri in self.player_dict.keys():
                    self.player_dict[uri].update_status(p.Metadata, p.PlaybackStatus, get_unix_timestamp())
                    last_observation_uri_list.remove(uri)
                else:
                    self.player_dict[uri] = PlayerState(p.Metadata, p.PlaybackStatus)
        for uri in last_observation_uri_list:
            del self.player_dict[uri]

    def scrobble_all_players(self):
        for uri, player_obj in self.player_dict.items():
            if player_obj.playback_status == "Playing":
                self.network.update_now_playing(
                    artist=player_obj.artist,
                    title=player_obj.title,
                    album=player_obj.album,
                    album_artist=player_obj.albumArtist,
                    track_number=player_obj.trackNumber,
                )
            if player_obj.total_played_time >= min(self.scrobble_time_threshold, int(player_obj.length / 2)) and not player_obj.if_scrobbled:
                self.network.scrobble(
                    artist=player_obj.artist, 
                    title=player_obj.title,
                    timestamp=player_obj.last_observation_timestamp,
                    album=player_obj.album,
                    album_artist=player_obj.albumArtist,
                    track_number=player_obj.trackNumber,
                    duration=int(player_obj.length)
                )
                player_obj.if_scrobbled = True
                self.logger.debug("scrobbled track: " + player_obj.title)
                self.logger.debug("artist: " + player_obj.artist)
                self.logger.debug("timestamp: " + str(player_obj.last_observation_timestamp))
                self.logger.debug("album: " + player_obj.album)
                self.logger.debug("albumArtist: " + player_obj.albumArtist)
                self.logger.debug("trackNumber: " + str(player_obj.trackNumber))
                self.logger.debug("duration: " + str(int(player_obj.length)))
                self.logger.debug("played time: " + str(int(player_obj.total_played_time)))
            else:
                # self.logger.debug("scrobble condition unmet")
                pass

    def update_now_playing(self):
        pass

@click.command()
@click.argument("config_file")
def main(config_file):
    from dbus.mainloop.glib import DBusGMainLoop
    import yaml

    dbus_loop = DBusGMainLoop(set_as_default=True)

    # load config
    with open(config_file, "r") as file:
        config = yaml.safe_load(file)

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
