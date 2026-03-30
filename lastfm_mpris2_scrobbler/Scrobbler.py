import pylast
from mpris2 import get_players_uri, Player
import fnmatch
from urllib import request
from urllib.error import URLError
from pathlib import Path
from PIL import Image

from lastfm_mpris2_scrobbler.globals import logger, get_unix_timestamp
from lastfm_mpris2_scrobbler.PlayerState import PlayerState
from lastfm_mpris2_scrobbler.Cache import Cache
import coloredlogs

class Scrobbler:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        coloredlogs.install(level=kwargs["log_level"], logger=logger)
        self.player_dict: dict[str, PlayerState] = {} # key: player_uri

        self.network: pylast.LastFMNetwork | None = None
        self._init_network()
            
        # supports wildcard, see matches_whitelist() below
        self.application_whitelist: list[str] = kwargs["application_whitelist"]

        # scrobbler will upload if the track has been played for 4 mins or half the total length
        self.scrobble_time_threshold: int = int(kwargs["scrobble_time_threshold"])

        # now playing art and text file to write, if specified
        self.art_path: Path | None = None
        self.txt_path: Path | None = None

        base_dir = kwargs.get("now_playing_dir")
        art_path = kwargs.get("now_playing_art")
        txt_path = kwargs.get("now_playing_txt")
        self.art_path = Path(art_path) if art_path else Path(base_dir, "now_playing.png") if base_dir else None
        self.txt_path = Path(txt_path) if txt_path else Path(base_dir, "now_playing.txt") if base_dir else None
        if base_dir and art_path and txt_path:
            logger.debug("Specifying now_playing_dir and both now_playing_art and now_playing_txt will ignore now_playing_dir.")
        try:
            if self.art_path:
                self.art_path.parent.mkdir(exist_ok=True, parents=True)
            if self.txt_path:
                self.txt_path.parent.mkdir(exist_ok=True, parents=True)
        except FileExistsError:
            if base_dir:
                raise FileExistsError("The now_playing_dir specified in the config.yaml " + base_dir + " includes a part which exists and is not a directory")
            elif art_path:
                raise FileExistsError("The now_playing_art specified in the config.yaml " + art_path + " includes a part which exists and is not a directory")
            elif txt_path:
                raise FileExistsError("The now_playing_txt specified in the config.yaml " + txt_path + " includes a part which exists and is not a directory")
        if self.art_path:
            self.art_path.touch()
        if self.txt_path:
            self.txt_path.touch()

        # offline cache
        self.cache = Cache()

    def connect_to_all_players(self):
        last_observation_uri_list = list(self.player_dict)
        for uri in get_players_uri():
            uri = str(uri)
            if self._matches_whitelist(uri):
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
            self._init_network()
        scrobble_list = []
        for uri, player_obj in self.player_dict.items():
            if player_obj.playback_status == "Playing" and self.network is not None:
                try:
                    self.network.update_now_playing(
                        artist=player_obj.artist,
                        title=self._fix_title(player_obj.title),
                        album=player_obj.album,
                        album_artist=player_obj.albumArtist,
                        track_number=player_obj.trackNumber,
                    )
                except Exception as e:
                    logger.error(f"Failed to report now playing status")
                if self.art_path:
                    try:
                        Image.open(request.urlopen(player_obj.artUrl)).save(self.art_path)
                    except ValueError:
                        logger.debug("The file specified at " + str(self.art_path) + " was insufficient to determine album art image format. Please specify an extension.")
                    except OSError as e:
                        logger.debug("Unable to write the file at " + str(self.art_path) + " (" + e.strerror + ")")
                    except URLError as e:
                        logger.debug("Unable to load URL at " + player_obj.artUrl + " (" + e.strerror + ")")
                    logger.info("Updated album art at " + str(self.art_path))
                if self.txt_path:
                    self.txt_path.write_text(player_obj.artist + " - " + self._fix_title(player_obj.title))
                    logger.info("Updated now playing file at " + str(self.txt_path))
            if player_obj.total_played_time >= min(self.scrobble_time_threshold, int(player_obj.length / 2)) and not player_obj.if_scrobbled:
                scrobble_list.append(player_obj)
                player_obj.if_scrobbled = True
            else:
                logger.debug("scrobble condition unmet")

        if self.network is not None:
            self._scrobble_list(scrobble_list, isCache=False)
            # [(trackid, artist, title, timestamp, album, album_artist, track_number, duration), ...]
            cache_list = self.cache.read_unscrobbled()
            if cache_list is not None:
                cache_list_converted = []
                for cache in cache_list:
                    cache_list_converted.append(PlayerState().set_value(
                        album=cache[4],
                        album_artist=cache[5],
                        artist=cache[1],
                        duration=cache[7],
                        timestamp=cache[3],
                        title=cache[2],
                        track_number=cache[6],
                        trackid=cache[0]
                    ))
                self._scrobble_list(cache_list_converted, isCache=True)
        elif len(scrobble_list) > 0:
            self.cache.write_unscrobbled(scrobble_list)
            logger.debug("Fail to scrobble now. Write to cache")
    
    def _fix_title(self, title):
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

    def _init_network(self):
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

    def _matches_whitelist(self, uri):
        """Check if URI matches any pattern in the whitelist."""
        for pattern in self.application_whitelist:
            if fnmatch.fnmatch(uri, pattern):
                return True
        return False

    def _obj_list_to_dict_list(self, obj_list: list[PlayerState]):
        dict_list = []
        for obj in obj_list:
            dict_list.append(
                {
                    "album": obj.album,
                    "album_artist": obj.albumArtist,
                    "artist": obj.artist,
                    "duration": obj.length,
                    "timestamp": obj.last_observation_timestamp,
                    "title": self._fix_title(obj.title),
                    "track_number": obj.trackNumber
                }
            )
        return dict_list
    
    def _scrobble_list(self, obj_list, isCache = False):
        if obj_list != None and len(obj_list) > 0:
            dict_list = self._obj_list_to_dict_list(obj_list)
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
