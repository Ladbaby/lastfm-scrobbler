
import pylast
from mpris2 import get_players_uri, Player

from lastfm_mpris2_scrobbler.globals import logger, get_unix_timestamp
from lastfm_mpris2_scrobbler.PlayerState import PlayerState

class Scrobbler:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.player_dict = {}

        # TODO: handle network error
        self.network = None
        self.init_network()
            
        self.application_whitelist = kwargs["application_whitelist"]

        self.now_playing_tracks_dict = {}
        for app in self.application_whitelist:
            self.now_playing_tracks_dict[app] = ""

        # scrobbler will upload if the track has been played for 4 mins or half the total length
        self.scrobble_time_threshold = 4 * 60

    def init_network(self):
        try:
            logger.debug("Try logging in now...")
            self.network = pylast.LastFMNetwork(
                api_key=self.kwargs["api_key"],
                api_secret=self.kwargs["api_secret"],
                username=self.kwargs["user_name"],
                password_hash=self.kwargs["password_hash"],
            )
            logger.info(f"Successfully login to Last.fm as {self.kwargs['user_name']}")
        except Exception as e:
            logger.debug(f"LastFMNetwork initialization failed: {e=}")
            logger.warning("Running in OFFLINE mode")

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
        if self.network is not None:
            for uri, player_obj in self.player_dict.items():
                if player_obj.playback_status == "Playing":
                    try:
                        self.network.update_now_playing(
                            artist=player_obj.artist,
                            title=player_obj.title,
                            album=player_obj.album,
                            album_artist=player_obj.albumArtist,
                            track_number=player_obj.trackNumber,
                        )
                    except Exception as e:
                        logger.error(f"Failed to report now playing status: {e=}")
                if player_obj.total_played_time >= min(self.scrobble_time_threshold, int(player_obj.length / 2)) and not player_obj.if_scrobbled:
                    try:
                        self.network.scrobble(
                            artist=player_obj.artist, 
                            title=player_obj.title,
                            timestamp=player_obj.last_observation_timestamp,
                            album=player_obj.album,
                            album_artist=player_obj.albumArtist,
                            track_number=player_obj.trackNumber,
                            duration=int(player_obj.length)
                        )
                    except Exception as e:
                        logger.error(f"Failed to scrobble: {e=}")
                    player_obj.if_scrobbled = True
                    logger.debug("scrobbled track: " + player_obj.title)
                    logger.debug("artist: " + player_obj.artist)
                    logger.debug("timestamp: " + str(player_obj.last_observation_timestamp))
                    logger.debug("album: " + player_obj.album)
                    logger.debug("albumArtist: " + player_obj.albumArtist)
                    logger.debug("trackNumber: " + str(player_obj.trackNumber))
                    logger.debug("duration: " + str(int(player_obj.length)))
                    logger.debug("played time: " + str(int(player_obj.total_played_time)))
                else:
                    logger.debug("scrobble condition unmet")
                    pass
        else:
            self.init_network()