
import pylast
from mpris2 import get_players_uri, Player

from lastfm_mpris2_scrobbler.globals import logger, get_unix_timestamp
from lastfm_mpris2_scrobbler.PlayerState import PlayerState
from lastfm_mpris2_scrobbler.Cache import Cache
import coloredlogs

class Scrobbler:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        coloredlogs.install(level=kwargs["log_level"], logger=logger)
        self.player_dict = {}

        # TODO: handle network error
        self.network = None
        self.init_network()
            
        self.application_whitelist = kwargs["application_whitelist"]

        self.now_playing_tracks_dict = {}
        for app in self.application_whitelist:
            self.now_playing_tracks_dict[app] = ""

        # scrobbler will upload if the track has been played for 4 mins or half the total length
        self.scrobble_time_threshold = int(kwargs["scrobble_time_threshold"])

        # offline cache
        self.cache = Cache()

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
        if self.network is None:
            self.init_network()
        scrobble_list = []
        for uri, player_obj in self.player_dict.items():
            if player_obj.playback_status == "Playing" and self.network is not None:
                try:
                    self.network.update_now_playing(
                        artist=player_obj.artist,
                        title=self.fix_title(player_obj.title),
                        album=player_obj.album,
                        album_artist=player_obj.albumArtist,
                        track_number=player_obj.trackNumber,
                    )
                except Exception as e:
                    logger.error(f"Failed to report now playing status")
            if player_obj.total_played_time >= min(self.scrobble_time_threshold, int(player_obj.length / 2)) and not player_obj.if_scrobbled:
                scrobble_list.append(player_obj)
                player_obj.if_scrobbled = True
            else:
                logger.debug("scrobble condition unmet")

        if self.network is not None:
            self.scrobble_list(scrobble_list, isCache=False)
            # [(trackid, artist, title, timestamp, album, album_artist, track_number, duration), ...]
            cache_list = self.cache.read_unscrobbled()
            if cache_list is not None:
                cache_list_converted = []
                for cache in cache_list:
                    cache_list_converted.append(PlayerState().set_value(
                        trackid=cache[0],
                        artist=cache[1],
                        title=cache[2],
                        timestamp=cache[3],
                        album=cache[4],
                        album_artist=cache[5],
                        track_number=cache[6],
                        duration=cache[7]
                    ))
                self.scrobble_list(cache_list_converted, isCache=True)
        elif len(scrobble_list) > 0:
            self.cache.write_unscrobbled(scrobble_list)
            logger.debug("Fail to scrobble now. Write to cache")

    def scrobble_list(self, obj_list, isCache = False):
        if obj_list != None and len(obj_list) > 0:
            dict_list = self.obj_list_to_dict_list(obj_list)
            try:
                self.network.scrobble_many(dict_list)
                logger.info("scrobbled: " + str(dict_list))
                if isCache:
                    self.cache.remove_unscrobbled(obj_list)
            except Exception as e:
                if not isCache:
                    self.cache.write_unscrobbled(obj_list)
                    logger.debug("Fail to scrobble now. Write to cache")
                else:
                    logger.debug("Fail to scrobble cached record now")
                    pass

    def obj_list_to_dict_list(self, obj_list):
        dict_list = []
        for obj in obj_list:
            dict_list.append(
                {
                    "artist": obj.artist,
                    "title": self.fix_title(obj.title),
                    "timestamp": obj.last_observation_timestamp,
                    "album": obj.album,
                    "album_artist": obj.albumArtist,
                    "track_number": obj.trackNumber,
                    "duration": obj.length,
                }
            )
        return dict_list
    
    def fix_title(self, title):
        audio_formats = [
            '.mp3', 
            '.ogg', 
            '.wav', 
            '.aac', 
            '.flac'
        ]
        for format in audio_formats:
            if title.endswith(format):
                return title[:-(len(format))]
        return title
