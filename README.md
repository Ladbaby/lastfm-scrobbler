# 🎵 Last.fm scrobbler

A Last.fm scrobbler via MPRIS2 in Linux, implemented via [pylast](https://github.com/pylast/pylast) and [mpris2](https://pythonhosted.org/mpris2/index.html)

Modified based on [dbus-scrobbler](https://github.com/spezifisch/dbus-scrobbler)

## Features

- [x] scrobble music to Last.fm if one of the conditions are met:

    - played for 4 mins
    - played for half the length
- [x] update now playing status
- [x] offline scrobble cache support

## What is MPRIS2?

> MPRIS (Media Player Remote Interfacing Specification) is a standard D-Bus (Desktop Bus) interface that allows applications to communicate with and control media players running on a Linux desktop environment.

Thus, this scrobbler is a general-purpose one under the Linux desktop environment, supporting scrobble music from media players without a built-in Last.fm scrobbling feature.

Check if your media player supports MPRIS2 via (make sure the player is running):

```bash
lastfm-mpris2-scrobbler --list-players
```

The uri names of players will be shown

## Installation

There're two options available now:

- grab the stand-alone binary from [release page](https://github.com/Ladbaby/lastfm-scrobbler/releases)

- or, via PyPI

    ```bash
    pip install lastfm-mpris2-scrobbler
    ```

## Configurations

The program expects a `config.yaml` file and can be placed wherever you like, for example `~/.config/lastfm-mpris2-scrobbler/`

Example and detailed information can be found in `config.yaml.example`:

```yaml
# username for that service
user_name: foo

# md5 hash of your password (obtained via `echo -n password | md5sum`)
password_hash: abc123492abccf4f1997f7ccaabc123b

# last.fm api, which can be created via https://www.last.fm/api/account/create
api_key: 11111111111111111111111111111111
api_secret: 11111111111111111111111111111111

# the app's uri you want to scrobble
# use `lastfm-mpris2-scrobbler --list-players` to check the uri name
application_whitelist: [ "org.mpris.MediaPlayer2.harmonoid" ]

# app's log level
log_level: DEBUG
```

## Usage

```bash
lastfm-mpris2-scrobbler -c PATH_TO_YOUR_CONFIG/config.yaml
```

For more options, see:

```bash
lastfm-mpris2-scrobbler --help
```

---

If you want to run it as a daemon service, here's a systemd service in user space for reference:

```ini
[Unit]
Description=Last.fm scrobbler via MPRIS2
Documentation=https://github.com/Ladbaby/lastfm-scrobbler

[Service]
ExecStart=PATH_TO_YOUR_BIN/lastfm-mpris2-scrobbler -c PATH_TO_YOUR_CONFIG/config.yaml

[Install]
WantedBy=default.target
```

You'll have to place the service file under `~/.config/systemd/user/` and name it like `scrobbler.service`

To run the daemon:

```shell
systemctl --user start scrobbler.service
```

To run at user login:

```shell
systemctl --user enable scrobbler.service
```

## Alternatives

If you'd like a scrobbler similar to this, there're some choices. I recommand taking a look at [scrobblez](https://github.com/YodaEmbedding/scrobblez). It additionally provides Spotify related improvement, but doesn't provide stand-alone binary build for installation.

Also, although [rescrobbled](https://github.com/InputUsername/rescrobbled) may also work, in my case it raised "Dbus error: argument type mismatch".

## Known Issues

- ~~If the music title contains unwanted substring (like `.mp3`), then Last.fm won't accept the scrobble~~

    The program can now remove some of the unwanted substrings, including:

    - `.mp3`
    - `.ogg`
    - `.wav`
    - `.acc`
    - `.flac`
