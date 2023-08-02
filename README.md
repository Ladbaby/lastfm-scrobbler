# Last.fm scrobbler

A Last.fm scrobbler via MPRIS2 in Linux, implemented via [pylast](https://github.com/pylast/pylast) and [mpris2](https://pythonhosted.org/mpris2/index.html)

Modified based on [dbus-scrobbler](https://github.com/spezifisch/dbus-scrobbler)

## Features

- [*] scrobble music to Last.fm if one of the conditions are met:

    - played for 4 mins
    - played for half the length
- [] scrobble now playing status
- [] offline storage support

## Alternatives

If you'd like a scrobbler similar to this, there're some choices. I recommand taking a look at [scrobblez](https://github.com/YodaEmbedding/scrobblez), which is more functional (at least for now).

Also, although [rescrobbled](https://github.com/InputUsername/rescrobbled) may also work, in my case it raised "Dbus error: argument type mismatch".

## What is MPRIS2?

> MPRIS (Media Player Remote Interfacing Specification) is a standard D-Bus (Desktop Bus) interface that allows applications to communicate with and control media players running on a Linux desktop environment.

Thus, this scrobbler is a general-purpose one under the Linux desktop environment, supporting scrobble music from media players without a built-in Last.fm scrobbling feature.

Check if your media player supports MPRIS2 via [playerctl](https://github.com/altdesktop/playerctl) (when it is running)

```bash
playerctl --list-all
```

## Installation

```bash
pip install -r requirements.txt
```

## Configurations

```bash
cp config.yaml.example config.yaml
vim config.yaml
```

details can be found in the config file

## Usage

```bash
python main.py config.yaml
```

