# Chrome Extension Backend

## ffmpeg commands

### Extract audio from video

Extract raw audio to `aac` format. Y
ou can change `aac` to `flac` as well.

```shell
ffmpeg -i input.mkv -vn -c:a copy output.aac
```

Extract audio and re-encode to mp3. You can increase the `-q:a` value form 2 to a higher value in order to get a smaller lower quality audio.

```shell
ffmpeg -i test_rec.mkv -vn -c:a libmp3lame -q:a 2 output.mp3
```

Extract audio and compress to mp3 using bitrate flag. A lower bitrate produces a lower quality and smaller audio file.

```shell
ffmpeg -i test_rec.mkv -vn -c:a libmp3lame -b:a 64k output.mp3
```

Same thing as above but for `aac` format

```shell
ffmpeg -i test_rec.mkv -vn -c:a aac -b:a 48k output.aac
```
