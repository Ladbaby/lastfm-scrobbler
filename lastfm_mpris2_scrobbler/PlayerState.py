from typing import Literal

from lastfm_mpris2_scrobbler.globals import logger, get_unix_timestamp

class PlayerState:
    def __init__(
        self, 
        metadata_dict: dict = None, 
        playback_status: Literal["Playing", "Paused", "Stopped"] = "Playing"
    ) -> None:
        # initialize all data members with default values
        self.if_scrobbled: bool = False
        self.playback_status: str = playback_status # record the playback status in observation. Must be 'Playing', 'Paused' or 'Stopped'.
        self.total_played_time: int = 0

        self.album: str = ''
        self.albumArtist: str = ''
        self.artist: str = ''
        self.artUrl: str = '' # image file path
        self.discNumber: int = 1
        self.firstUsed: str = ''
        self.last_observation_timestamp: int = get_unix_timestamp() # record the timestamp of last observation
        self.length: int = 1 # time length of the current song in seconds
        self.title: str = ''
        self.trackid: str = ''
        self.trackNumber: int = 1
        self.url: str = ''

        if metadata_dict is not None:
            self.update_status(metadata_dict, playback_status, self.last_observation_timestamp)

    def set_value(
        self, 
        album: str, 
        album_artist: str, 
        artist: str, 
        duration: int,
        timestamp: int, 
        title: str, 
        track_number: int, 
        trackid: str
    ):
        self.album = album
        self.albumArtist = album_artist
        self.artist = artist
        self.length = duration
        self.last_observation_timestamp = timestamp
        self.title = title
        self.trackNumber = track_number
        self.trackid = trackid
        return self
    
    def update_status(
        self, 
        metadata_dict: dict, 
        playback_status: Literal["Playing", "Paused", "Stopped"], 
        timestamp: int
    ):
        # reset status if the track change
        # some players won't update trackid, so we use the title and artist as an additional condition
        if self.trackid == self._get_value_from_dict(metadata_dict, "mpris:trackid") and self.title == self._get_value_from_dict(metadata_dict, "xesam:title"):
            self.total_played_time += (timestamp - self.last_observation_timestamp) if playback_status == "Playing" else 0
        else:
            self.total_played_time = 0
            self.if_scrobbled = False

        self.album = self._get_value_from_dict(metadata_dict, "xesam:album")
        self.albumArtist = self._handle_multiple_artists(self._get_value_from_dict(metadata_dict, "xesam:albumArtist", expect_type="list"))
        self.artist = self._handle_multiple_artists(self._get_value_from_dict(metadata_dict, "xesam:artist", expect_type="list"))
        self.artUrl = self._get_value_from_dict(metadata_dict, "mpris:artUrl")
        self.discNumber = self._get_value_from_dict(metadata_dict, "xesam:discNumber", expect_type="int")
        self.firstUsed = self._get_value_from_dict(metadata_dict, "xesam:firstUsed")
        self.last_observation_timestamp = timestamp
        self.length = int(self._get_value_from_dict(metadata_dict, "mpris:length", expect_type="int") / 1000000)
        self.playback_status = playback_status
        self.title = self._get_value_from_dict(metadata_dict, "xesam:title")
        self.trackid = self._get_value_from_dict(metadata_dict, "mpris:trackid")
        self.trackNumber = self._get_value_from_dict(metadata_dict, "xesam:trackNumber", expect_type="int")
        self.url = self._get_value_from_dict(metadata_dict, "xesam:url")

        # Handle some special cases
        if self.albumArtist in ["", []]:
            self.albumArtist = self.artist
        if self.url == "":
            self.url = "/"

    def _get_value_from_dict(self, dict: dict, key: str, expect_type: str = "str"):
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

    def _handle_multiple_artists(self, artist_array: list[str]) -> str:
        # convert artist array into a single string
        return ", ".join(artist_array)
