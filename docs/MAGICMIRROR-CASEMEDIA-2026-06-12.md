# MagicMirror Case Media Module

## Purpose

This note records the custom `MMM-CaseMedia` module added on `2026-06-12` for local image and video playback on the Orange Pi display.

## Source Location

The module source is stored in this repo at:

- `magicmirror-modules/MMM-CaseMedia`

The live module on the Orange Pi is at:

- `/home/lazuli/MagicMirror/modules/MMM-CaseMedia`

## What It Does

- scans a local media folder on the Pi
- displays images and videos in a loop
- supports timed image display
- supports timed video display
- can loop videos during the configured display window
- supports muted video playback
- can run as a full-screen background or as a widget
- supports `original`, `rounded`, `square`, and `circle` shapes for widget mode
- supports `cover`, `contain`, `fill`, and `scale-down` media fitting

## Active Configuration

The live MagicMirror config currently enables the module as a background:

- module: `MMM-CaseMedia`
- position: `fullscreen_below`
- media path: `public/media`
- refresh interval: `30000`
- sort order: `modified`
- random order: `true`
- image duration: `15000`
- video duration: `30000`
- video loop: `true`
- video muted: `true`
- fit mode: `cover`
- display mode: `background`
- background dimmer: `0.12`

## Media Folder

Add files here on the Orange Pi:

- `/home/lazuli/MagicMirror/modules/MMM-CaseMedia/public/media`

Supported image formats:

- `.jpg`
- `.jpeg`
- `.png`
- `.gif`
- `.webp`
- `.bmp`

Supported video formats:

- `.mp4`
- `.webm`
- `.mov`
- `.m4v`

## Notes

- The module refreshes the media list every `30` seconds, so new files should appear without restarting MagicMirror.
- With `videoDuration > 0`, videos stay on screen for the configured time and can loop during that window.
- With `videoDuration <= 0`, a video plays once and advances on `ended`.
- The current page will show an empty-state message until files are added to the media folder.

## Validation

Verified on `2026-06-12`:

- MagicMirror service restarted cleanly
- `MMM-CaseMedia` node helper loaded on startup
- browser loaded `modules/MMM-CaseMedia/MMM-CaseMedia.js`
- empty-state text rendered on the page when the media folder was empty
