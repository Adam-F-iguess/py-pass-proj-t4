Pygame Paint + Frame Renderer

What this does
- Plays a sequence of image frames stored in `assets/frames/`.
- Lets you draw an overlay (paint) on top of frames and save combined frames to `assets/output/`.
- Optional audio support: place an audio file at `assets/audio.mp3` (or pass `--audio <path>`).

Important copyright note
- This project does not bundle or provide copyrighted media (e.g., "Bad Apple").
- You must provide your own frames and audio files.

Where to put files
- Frames: `assets/frames/` — supported formats: PNG/JPG/JPEG/BMP. Name frames so they sort in playback order (e.g., `00001.png`, `00002.png`, ...).
- Audio: `assets/audio.mp3` (default), or pass `--audio <path>` when running. OGG works best for seeking on many platforms; MP3 seeking can be inconsistent across backends.
 - Audio: `assets/audio.mp3` (default), or place songs in `assets/music/` and accompanying frames in `assets/videos/<song-name>/`.
	 The player will show a selection screen at startup when tracks are present in `assets/music/`.
- Output: `assets/output/` (created automatically) — saved combined frames will appear here when you press `s`.

How to run
1. Install dependencies:
```powershell
python -m pip install --upgrade pip
python -m pip install pygame
```

2. Run the player:
```powershell
python main.py
# Audio: the player will attempt to load `assets/audio.mp3` and auto-start playback if present.
# To explicitly specify a different audio file:
python main.py --audio assets/audio.mp3
# To explicitly disable audio even if present:
python main.py --no-audio
```

Controls
- Mouse left-drag: draw
- Mouse right-drag: erase
- Space: play / pause (also pauses/unpauses audio)
- Left/Right or typed `[` / `]`: when paused, step frames
- c: clear overlay
- s: save combined current frame + overlay to `assets/output/`
- +/-: increase / decrease brush size
- ESC: quit

Troubleshooting
- "No video mode has been set" errors: make sure you run the updated `main.py` in this repo. I changed the code to avoid calling `convert()` before the display is set; re-run `python main.py`.
- If seeking audio doesn't work: try using an OGG audio file. MP3 seeking depends on your SDL_mixer backend and may be unreliable.
- If you see traceback referencing `K_BRACKETRIGHT`: update to the latest `main.py` (this repo already uses `ev.unicode` to accept `[`/`]` typed keys).

If you want, I can add:
- A demo generator that creates a few synthetic frames + demo audio so you can test the full A/V pipeline without providing assets.
- A batch-export feature (apply current overlay to every frame and write combined images to `assets/output/`).

