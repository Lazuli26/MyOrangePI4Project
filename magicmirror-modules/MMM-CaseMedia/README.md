# MMM-CaseMedia

Custom MagicMirror module for showing local images and videos either as a full-screen background or as a shaped widget.

## Media Folder

Put files in:

`/home/lazuli/MagicMirror/modules/MMM-CaseMedia/public/media`

Supported files:

- Images: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`
- Videos: `.mp4`, `.webm`, `.mov`, `.m4v`

## Example Config

```js
{
  module: "MMM-CaseMedia",
  position: "fullscreen_below",
  config: {
    mediaPath: "public/media",
    refreshInterval: 30000,
    randomOrder: true,
    imageDuration: 10000,
    videoDuration: 30000,
    videoLoop: true,
    videoMuted: true,
    fitMode: "contain",
    positionPreset: "center-center",
    objectPosition: "",
    displayMode: "background",
    backgroundDimmer: 0
  }
}
```

## Widget Example

```js
{
  module: "MMM-CaseMedia",
  position: "middle_center",
  config: {
    mediaPath: "public/media/widget",
    displayMode: "widget",
    shape: "circle",
    widgetWidth: "260px",
    imageDuration: 8000,
    videoDuration: 20000,
    fitMode: "cover"
  }
}
```

## Notes

- `videoDuration > 0` means a video stays visible for that many milliseconds.
- With `videoLoop: true`, the video loops until the module advances to the next file.
- `videoDuration <= 0` means a video plays through once and advances on `ended`.
- `shape` accepts `original`, `rounded`, `square`, or `circle`.
- `fitMode` accepts `cover`, `contain`, `fill`, or `scale-down`.
- `positionPreset` accepts `top-left`, `top-center`, `top-right`, `center-left`, `center-center`, `center-right`, `bottom-left`, `bottom-center`, or `bottom-right`.
- `objectPosition` accepts any CSS `object-position` value such as `50% 50%`, `center top`, `left center`, or `80% 20%`. When set, it overrides `positionPreset`.

## Portrait Display Tips

For a very narrow portrait panel like `480x1920`:

- use `fitMode: "contain"` if you want to see the whole video without cropping
- use `fitMode: "cover"` if you want edge-to-edge fill and accept cropping
- use `positionPreset` or `objectPosition` to choose which part of the media stays visible when using `cover`
- use `zoom: 1` in the main MagicMirror config so the viewport matches the panel more directly
