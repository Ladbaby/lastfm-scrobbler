from lastfm_mpris2_scrobbler.globals import get_unix_timestamp
from lastfm_mpris2_scrobbler.globals import logger

class PlayerState:
    def __init__(self, metadata_dict = None, playback_status = "Playing") -> None:
        self.total_played_time = 0
        self.last_observation_timestamp = get_unix_timestamp()
        self.trackid = ""
        self.if_scrobbled = False
        if metadata_dict is not None:
            self.update_status(metadata_dict, playback_status, self.last_observation_timestamp)

    def set_value(self, trackid, artist, title, timestamp, album, album_artist, track_number, duration):
        self.trackid = trackid
        self.artist = artist
        self.title = title
        self.last_observation_timestamp = timestamp
        self.album = album
        self.albumArtist = album_artist
        self.trackNumber = track_number
        self.length = duration
        return self

    def handle_multiple_artists(self, artist_array):
        # convert artist array into a single string
        return ", ".join(artist_array)
    
    def update_status(self, metadata_dict, playback_status, timestamp):
        # time length of the current song in seconds
        self.length = int(self.get_value_from_dict(metadata_dict, "mpris:length", expect_type="int") / 1000000)
        # image file path
        self.artUrl = self.get_value_from_dict(metadata_dict, "mpris:artUrl")
        self.album = self.get_value_from_dict(metadata_dict, "xesam:album")
        self.artist = self.handle_multiple_artists(self.get_value_from_dict(metadata_dict, "xesam:artist", expect_type="list"))
        self.albumArtist = self.handle_multiple_artists(self.get_value_from_dict(metadata_dict, "xesam:albumArtist", expect_type="list"))
        if self.albumArtist == "":
            self.albumArtist = self.artist
        self.discNumber = self.get_value_from_dict(metadata_dict, "xesam:discNumber", expect_type="int")
        self.firstUsed = self.get_value_from_dict(metadata_dict, "xesam:firstUsed")
        self.title = self.get_value_from_dict(metadata_dict, "xesam:title")
        self.trackNumber = self.get_value_from_dict(metadata_dict, "xesam:trackNumber", expect_type="int")
        self.url = self.get_value_from_dict(metadata_dict, "xesam:url")
        if self.url == "":
            self.url = "/"

        # record the timestamp of last observation
        if self.trackid == self.get_value_from_dict(metadata_dict, "mpris:trackid"):
            self.total_played_time += (timestamp - self.last_observation_timestamp) if playback_status == "Playing" else 0
        else:
            self.total_played_time = 0
            self.if_scrobbled = False
        self.trackid = self.get_value_from_dict(metadata_dict, "mpris:trackid")
        self.last_observation_timestamp = timestamp

        # record the playback status in observation
        # May be 'Playing', 'Paused' or 'Stopped'.
        self.playback_status = playback_status

    def get_value_from_dict(self, dict: dict, key: str, expect_type: str = "str"):
        try:
            value = dict[key]
            if expect_type == "str":
                return str(value)
            elif expect_type == "int":
                return int(value)
            elif expect_type == "list":
                return value
            else:
                logger.exception(f"Unexpected {expect_type=}")
        except Exception as e:
            logger.debug(f"Failed to retrieve {key=} from player. Value for this key is set to default")
            if expect_type == "str":
                return ""
            elif expect_type == "int":
                return 1
            elif expect_type == "list":
                return []
            else:
                logger.exception(f"Unexpected {expect_type=}")
