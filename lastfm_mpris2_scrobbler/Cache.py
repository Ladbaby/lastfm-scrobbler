import os
import sqlite3
from xdg.BaseDirectory import xdg_cache_home

from lastfm_mpris2_scrobbler.globals import logger

class Cache:
    def __init__(self) -> None:
        data_path = os.path.join(xdg_cache_home, "lastfm-mpris2-scrobbler")
        db_cache_path = os.path.join(data_path, "unscrobbled.db")
        logger.debug(db_cache_path)
        # db_history_path = os.path.join(data_path, "history.db")

        os.makedirs(data_path, exist_ok=True)
        try:
            self.db_cache_conn = sqlite3.connect(db_cache_path)
            self.db_cache_cursor = self.db_cache_conn.cursor()
            self.db_cache_cursor.execute('''
                CREATE TABLE IF NOT EXISTS records (
                    trackid TEXT PRIMARY KEY,
                    artist TEXT,
                    title TEXT,
                    timestamp INTEGER,
                    album TEXT,
                    album_artist TEXT,
                    track_number INTEGER,
                    duration INTEGER
                )
            ''')
            self.db_cache_conn.commit()
        except Exception as e:
            logger.error(e)
            exit(1)

    def read_unscrobbled(self):
        try:
            self.db_cache_cursor.execute('''
                SELECT * FROM records
            ''')
            # return a list of tuple, each represent a record
            return self.db_cache_cursor.fetchall()
        except Exception as e:
            logger.error(e)
            return None
        
    def write_unscrobbled(self, unscrobbled_list):
        try:
            for record in unscrobbled_list:
                self.db_cache_cursor.execute('''
                    INSERT INTO records (trackid, artist, title, timestamp, album, album_artist, track_number, duration)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (record.trackid, record.artist, record.title, record.last_observation_timestamp, record.album, record.albumArtist, record.trackNumber, record.length))
                self.db_cache_conn.commit()
        except Exception as e:
            logger.error(e)

    def remove_unscrobbled(self, remove_list):
        try:
            for record in remove_list:
                self.db_cache_cursor.execute('''
                    DELETE FROM records WHERE trackid = ?
                ''', (record.trackid,))
                self.db_cache_conn.commit()
        except Exception as e:
            logger.error(e)



