# Apple Music ALAC / Dolby Atmos Downloader

Original script by Sorrow. Credit to [@zhaarey](https://github.com/zhaarey) and modified by me to include some fixes and improvements.

> [!IMPORTANT]
> Install MP4Box before continuing. Ensure it's correctly added to the environment variables.\
> You can do this by entering `apt install wget git golang gpac ffmpeg nano -y` in your terminal.

## New Features

- MP4Box will be called automatically to package EC3 as M4A file.
- Changed the directory structure to `ArtistName\AlbumName`; For Atmos files, its directory structure has changed to `ArtistName\AlbumName [Atmos]` and files are moved into `AM-DL-Atmos downloads`.
- Add support for overall completion status display upon finishing the run.
- Automatically embed cover art and LRC lyrics (requires `media-user-token`).
- Supports `check` with `main`, which can take a text address or API database.
- Add `get-m3u8-from-device` (set to `true`) and set port `adb forward tcp:20020 tcp:20020` to get M3U8 from the emulator.
- Add support templates for folders and files.
- Add support for downloading all albums from an artist: `go run main.go https://music.apple.com/us/artist/taylor-swift/159260351 --all-album`
- Add wrapper integration with its insane decryption speed rate (Supports Linux OS currently)
- Add support for length limitation with `limit-max` (default value of `limit-max` is 200).
- Add support for synchronized and unsynchronized lyrics.
- Add support for decoding files for arm64 platforms.

### Special thanks to `chocomint` for creating agent-arm64.js

### Supported Formats

- ALAC `(audio-alac-stereo)`
- EC3 `(audio-atmos / audio-ec3)`

For AAC downloads, it is recommended to use [WorldObservationLog's AppleMusicDecrypt](https://github.com/WorldObservationLog/AppleMusicDecrypt).

### Supported formats for AppleMusicDecrypt

- ALAC `(audio-alac-stereo)`
- EC3 `(audio-atmos / audio-ec3)`
- AC3 `(audio-ac3)`
- AAC `(audio-stereo)`
- AAC-binaural `(audio-stereo-binaural)`
- AAC-downmix `(audio-stereo-downmix)`

## How To Use

**1. Start up the decoding daemon:**

- With **frida server**:
    1. Create a virtual device on Android Studio with an image that doesn't have Google APIs.
    2. Install this version of Apple Music: [Apple Music 3.6.0 beta](https://www.apkmirror.com/apk/apple/apple-music/apple-music-3-6-0-beta-release/apple-music-3-6-0-beta-4-android-apk-download/). You will also need SAI to install it: [SAI on F-Droid](https://f-droid.org/pt_BR/packages/com.aefyr.sai.fdroid/).
    3. Launch Apple Music and sign in to your account (subscription required).
    4. Port forward 10020 TCP:
    ```sh
    adb forward tcp:10020 tcp:10020
    ```
    6. Start the **frida** agent with the command bellow:
        - For x86 platforms:
        ```sh
        frida -U -l agent.js -f com.apple.android.music
        ```
        - For arm64 platforms:
       ```sh
        frida -U -l agent-arm64.js -f com.apple.android.music
       ```
- With **wrapper**:
1. Run the following command to download **wrapper**:
```sh
wget "https://github.com/itouakirai/wrapper/releases/download/linux/wrapper.linux.x86_64.tar.gz" && mkdir wrapper && tar -xzf wrapper.linux.x86_64.tar.gz -C wrapper
```
2. Start the **wrapper daemon**:
- By command:
    1. `cd` to wrapper directory
    ```sh
    cd wrapper
    ```
    \
    2. Start the daemon with following command:
    ```sh
    ./wrapper -D 10020 -M 20020 -L username:password
    ```
    \
    Replace both `username` and `password` with your Apple Music account credentials.
    \
    \
    3. Once the service is running on background. move on to Step 2 by opening another terminal.

> [!WARNING]
> The following script is still in the testing stage; I do not guarantee the script will fully work.
- By **python script** (beta):
    1. Download the following file to your host and make it executable:
    ```sh
    wget "https://raw.githubusercontent.com/Yuzuk1Shimotsuki/apple-music-alac-atmos-downloader/main/wrapper.py"
    chmod +x wrapper.py
    ```
    \
    2. Run the code and enter your Apple Music credentials.
    \
    3. Once the service is moved to the background. move on to Step 2 in the same terminal. 

**2. Run the `main.go` file with your preferred options:**
- To download the whole album:
```sh
go run main.go https://music.apple.com/us/album/whenever-you-need-somebody-2022-remaster/1624945511
```

- To download some selected songs in the album: 
```sh
go run main.go --select https://music.apple.com/us/album/whenever-you-need-somebody-2022-remaster/1624945511
```
Once prompted, enter your numbers separated by spaces.
- To download the entire playlist: 
```sh
go run main.go https://music.apple.com/us/playlist/taylor-swift-essentials/pl.3950454ced8c45a3b0cc693c2a7db97b
``` 
or 
```sh
go run main.go https://music.apple.com/us/playlist/hi-res-lossless-24-bit-192khz/pl.u-MDAWvpjt38370N
```

- To download all albums from an artist:
```sh
go run main.go https://music.apple.com/us/artist/taylor-swift/159260351 --all-album
```

- To download songs with Dolby Atmos® support: 
```sh
go run main.go --atmos https://music.apple.com/us/album/1989-taylors-version-deluxe/1713845538
```

and replace the URL above with your vaild Apple Music URL

### For Downloading Lyrics

1. Open Apple Music and log in.
2. Open the Developer tools, Click `Application -> Storage -> Cookies -> https://music.apple.com`.
3. Find the cookie named `media-user-token` and copy its value.
4. Paste the cookie value obtained in step 3 into the `config.yaml` and save it.
5. Start the script as usual.

---

**Note:** For detailed instructions, please refer to [step 3 in the original documentation](https://telegra.ph/Apple-Music-Wrapper-On-WSL1-07-21) (available in Simplified Chinese only).
