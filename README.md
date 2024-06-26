# Uni - _The Last Multipurpose Bot, Ever_

<p align="center">
    <img src="./assets/repo/logo.png" width=200 />
</p>

From basic server management to fun games, music playback, and even AI interactions, Uni has got you covered.

<p align="center">
  <img src="https://img.shields.io/github/stars/notjawad/uni"  />
  <img src="https://img.shields.io/github/issues/notjawad/uni"  />
  <img src="https://img.shields.io/badge/LICENSE-MIT-green"  />
</p>

![Alt](https://repobeats.axiom.co/api/embed/8c8ffc71c338891e080c675e9d0ac2af8532feb9.svg "Repobeats analytics image")

## Features

- **Server Management:** Welcome/leave messages, server info control.
- **Moderation:** Kick, ban, manage threads, timeouts, and more.
- **Role Management:** Add, remove, modify roles, set permissions.
- **Message Handling:** Purge messages, nuke channels, set slowmode.
- **Logging & Security:** Enable/disable logging, anti-phishing, VirusTotal scan.
- **Media & Entertainment:** Music playback, LastFM, Spotify, Valorant profiles, Twitch notifications.
- **Utility Commands:** Timezone management, word definitions, server stats.

<details>
  <summary>View Screenshots</summary>
<img src="./assets/repo/music.png" width=1000/>
<img src="./assets/repo/queue.png" width=1000/>
<img src="./assets/repo/purge.png" width=1000/>
<img src="./assets/repo/git.png" width=1000/>
<img src="./assets/repo/minecraft.png" width=1000/>
<img src="./assets/repo/spotifyrec.png" width=1000/>
<img src="./assets/repo/lastfmnp.png" width=1000/>
<img src="./assets/repo/lastfmwhois.png" width=1000/>
<img src="./assets/repo/moviewatch.png" width=1000/>
<img src="./assets/repo/listeners.png" width=1000/>

</details>

# Todo

- [x] [**extensions/events.py:21**](./extensions/events.py#L21) - Implement welcome messages
- [ ] [**extensions/events.py:51**](./extensions/events.py#L51) - Implement leave messages
- [ ] [**extensions/events.py:53**](./extensions/events.py#L53) - Make reminder message look better
- [ ] [**extensions/github.py:12**](./extensions/github.py#L12) - Fix broken emojis
- [ ] [**extensions/information.py:393**](./extensions/information.py#L393) - Change this to use a select menu
- [ ] [**extensions/moderation.py:334**](./extensions/moderation.py#L334) - Implement role info command
- [ ] [**extensions/music.py:22**](./extensions/music.py#L22) - Music functionality is not working as expected. It needs to be fixed.
- [ ] [**extensions/spotify.py:4**](./extensions/spotify.py#L4) - Implement Spotify commands

## Self Hosting

If you want to self-host this bot, follow these steps:

1. Clone the repository:

```zsh
git clone https://github.com/notjawad/uni.git && cd uni
```

2. Install the required Python packages:

```zsh
python3 -m venv venv
python3 -m pip install -r requirements.txt
```

3. Rename [`config.example.yml`](./config.example.yml) file to `config.yml` and fill with your bot’s token and other configuration details.

```zsh
mv config.example.yml config.yml
```

4. Rename [`application.example.yml`](./application.example.yml) file to `application.yml` and fill with your Spotify tokens and other configuration details.

```zsh
mv application.example.yml application.yml
```

6. Download the latest Lavalink jar

```zsh
wget -P bin https://github.com/lavalink-devs/Lavalink/releases/download/4.0.4/Lavalink.jar
```

5. Run the bot and Lavalink server:

```zsh
java -jar bin/Lavalink.jar
```

```zsh
python3 main.py
```

Please note that you need Python 3.8 or higher to run this bot.

## Contribute

Uni is an open-source project, and contributions are welcome! If you have coding skills or want to contribute in other ways, feel free to get involved. Here's how you can contribute:

1. **Code Contributions:**

   - Fork the repository.
   - Create a new branch for your changes.
   - Make your improvements and submit a pull request.

2. **Bug Reports:**
   - Report any bugs or issues on the [GitHub Issues](https://github.com/notjawad/uni/issues) page.
   - Include detailed information about the problem and steps to reproduce it.
