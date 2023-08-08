from lastfm_mpris2_scrobbler.globals import get_unix_timestamp

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