"""
Pygame paint + frame renderer (no audio).

This program intentionally does NOT include any copyrighted media such as the
"Bad Apple" frames or audio. You must supply your own frame images in
`assets/frames/` if you want to render an existing animation. The app will
let you draw overlays (paint) and play the frames without audio.

Controls:
 - Mouse left-drag: draw
 - Mouse right-drag: erase
 - Space: play / pause
 - [ / ] or Left/Right arrows: previous / next frame when paused
 - c: clear overlay
 - s: save combined current frame + overlay to `assets/output/` (created if needed)
 - +/-: increase / decrease brush size
 - ESC or window close: quit

Usage:
 - Put frames into `assets/frames/` (png/jpg/etc.). Name them so they sort in order.
 - Run: python main.py --fps 30 --frames assets/frames

If no frames are present the app opens a blank canvas where you can draw and
play a simple looping empty-frame animation (useful for testing).
"""

import os
import time
import glob
import argparse
import pygame


ASSET_FRAMES_DIR = os.path.join("assets", "frames")
ASSET_AUDIO_PATH = os.path.join("assets", "audio.mp3")
OUTPUT_DIR = os.path.join("assets", "output")
DEFAULT_FPS = 30


def find_frame_files(frames_dir):
	if not os.path.isdir(frames_dir):
		return []
	exts = ["*.png", "*.jpg", "*.jpeg", "*.bmp"]
	files = []
	for e in exts:
		files.extend(glob.glob(os.path.join(frames_dir, e)))
	return sorted(files)


def load_frame_surface(path):
	try:
		surf = pygame.image.load(path)
		# Do not call convert()/convert_alpha() here — a display mode
		# may not yet be set and those functions require a video surface.
		return surf
	except Exception as e:
		print(f"Failed to load frame {path}: {e}")
		return None


def save_combined(frame_surf, overlay_surf, path):
	# Combine into a single surface and save as PNG
	w, h = frame_surf.get_size()
	out = pygame.Surface((w, h), pygame.SRCALPHA)
	out.blit(frame_surf, (0, 0))
	out.blit(overlay_surf, (0, 0))
	try:
		pygame.image.save(out, path)
		return True
	except Exception as e:
		print(f"Failed to save {path}: {e}")
		return False


def main():
	parser = argparse.ArgumentParser(description="The World's Worst Video Player")
	parser.add_argument("--fps", type=int, default=DEFAULT_FPS, help="Playback FPS")
	parser.add_argument("--frames", default=ASSET_FRAMES_DIR, help="Frames directory")
	parser.add_argument("--audio", default=ASSET_AUDIO_PATH, help="Path to audio file to play (optional)")
	parser.add_argument("--no-audio", action="store_true", help="Do not load or play audio even if present")
	args = parser.parse_args()

	# Ensure music/videos dirs exist for user to drop files
	os.makedirs(os.path.join("assets", "music"), exist_ok=True)
	os.makedirs(os.path.join("assets", "videos"), exist_ok=True)

	# Initialize pygame early so we can show a selection menu
	pygame.init()

	# Helper: scan assets/music for available audio tracks and map to video folders
	def scan_music_tracks():
		music_dir = os.path.join("assets", "music")
		exts = ["*.mp3", "*.ogg", "*.wav"]
		tracks = []
		for e in exts:
			for p in glob.glob(os.path.join(music_dir, e)):
				name = os.path.splitext(os.path.basename(p))[0]
				# associated video frames dir is assets/videos/<name>/
				video_dir = os.path.join("assets", "videos", name)
				has_video = os.path.isdir(video_dir) and len(find_frame_files(video_dir)) > 0
				tracks.append((p, name, has_video, video_dir))
		return sorted(tracks, key=lambda x: x[1].lower())

	# If there are tracks in assets/music, show a simple selector before playback
	def select_track_menu():
		tracks = scan_music_tracks()
		if not tracks:
			return None
		menu_w, menu_h = 640, 480
		menu_surf = pygame.display.set_mode((menu_w, menu_h))
		pygame.display.set_caption("The World's Worst Video Player")
		menu_clock = pygame.time.Clock()
		font = pygame.font.SysFont(None, 28)
		sel = 0
		running = True
		while running:
			menu_surf.fill((20, 20, 20))
			title = font.render("Select a song (Up/Down, Enter to play, Esc to quit)", True, (240, 240, 240))
			menu_surf.blit(title, (12, 12))
			y = 56
			for i, (path, name, has_video, video_dir) in enumerate(tracks):
				label = f"{name}  {'[video]' if has_video else ''}"
				color = (255, 255, 0) if i == sel else (200, 200, 200)
				txt = font.render(label, True, color)
				menu_surf.blit(txt, (24, y))
				y += 36
			pygame.display.flip()
			for ev in pygame.event.get():
				if ev.type == pygame.QUIT:
					return None
				if ev.type == pygame.KEYDOWN:
					if ev.key == pygame.K_ESCAPE:
						return None
					elif ev.key == pygame.K_UP:
						sel = max(0, sel - 1)
					elif ev.key == pygame.K_DOWN:
						sel = min(len(tracks) - 1, sel + 1)
					elif ev.key == pygame.K_RETURN or ev.key == pygame.K_KP_ENTER:
						return tracks[sel]
			menu_clock.tick(30)

	# Present selection menu if songs exist
	sel = select_track_menu()

	# Decide frames directory and audio path depending on selection
	if sel is None:
		frames_dir = args.frames
		audio_path = args.audio
	else:
		audio_path = sel[0]
		# use associated video folder if it has frames, otherwise default frames dir
		frames_dir = sel[3] if sel[2] else args.frames

	frame_files = find_frame_files(frames_dir)

	# Determine window size from first frame or default
	if frame_files:
		first = load_frame_surface(frame_files[0])
		if first is None:
			print("Failed to load first frame; using 800x600 canvas")
			w, h = 800, 600
			frame_surf = None
		else:
			w, h = first.get_size()
			frame_surf = first
	else:
		w, h = 800, 600
		frame_surf = None

	# Diagnostic prints to help when "nothing happens" — show what's found
	print(f"Starting player — frames={len(frame_files)}  canvas={w}x{h}")
	if len(frame_files) > 0:
		print("Sample frames:", ", ".join(frame_files[:3]))

	screen = pygame.display.set_mode((w, h))
	pygame.display.set_caption("The World's Worst Video Player")
	clock = pygame.time.Clock()

	fps = max(1, args.fps)

	# Audio setup
	# Keep any audio path chosen from the selection menu; fall back to args.audio
	if not sel:
		audio_path = args.audio
	# audio_enabled is true if audio not disabled and the file exists
	audio_enabled = (not args.no_audio) and os.path.isfile(audio_path)
	print(f"Audio path in use: {audio_path}  enabled={audio_enabled}")
	audio_started = False
	audio_paused_at = None
	audio_pause_acc = 0.0
	audio_start_time = None
	if audio_enabled:
		try:
			pygame.mixer.init()
			pygame.mixer.music.load(audio_path)
			print("Loaded audio:", audio_path)
		except Exception as e:
			print("Failed to initialize/load audio:", e)
			audio_enabled = False

	# Overlay surface for drawings (RGBA)
	overlay = pygame.Surface((w, h), pygame.SRCALPHA)

	brush_color = (255, 255, 255, 255)
	brush_radius = 6
	# audio volume (0.0 - 1.0)
	volume = 1.0
	muted = False

	playing = False
	frame_index = 0
	last_time = time.time()
	start_time = last_time

	# Prepare font and static HUD text to avoid per-frame allocations
	font = pygame.font.SysFont(None, 20)
	instr = "Space=Play/Pause  [ ] / Arrows=Frame  c=clear  s=save  +/- brush"
	instr_surf = font.render(instr, True, (200, 200, 200))

	# reuse erase surface when brush changes
	erase_surf = None

	def current_frame_surface(idx):
		if frame_files:
			path = frame_files[idx]
			surf = load_frame_surface(path)
			if surf is None:
				# Return an empty surface if load fails
				return pygame.Surface((w, h))
			# Scale first if needed
			if surf.get_size() != (w, h):
				surf = pygame.transform.smoothscale(surf, (w, h))
			# Convert now that a display mode exists
			if pygame.display.get_surface() is not None:
				try:
					surf = surf.convert_alpha() if surf.get_alpha() else surf.convert()
				except Exception:
					pass
			return surf
		else:
			# Blank background when no frames
			s = pygame.Surface((w, h))
			s.fill((30, 30, 30))
			return s

	# Preload current frame once
	cur_frame = current_frame_surface(frame_index)

	# If we loaded an initial frame before set_mode, convert it now
	if cur_frame is not None and pygame.display.get_surface() is not None:
		try:
			cur_frame = cur_frame.convert_alpha() if cur_frame.get_alpha() else cur_frame.convert()
		except Exception:
			# conversion isn't critical; continue with raw surface
			pass

	drawing = False
	erasing = False

	# If audio is enabled, auto-start audio and playback by default
	if audio_enabled:
		try:
			pygame.mixer.music.play(loops=-1)
			audio_started = True
			audio_start_time = time.time()
			playing = True
			last_time = time.time()
		except Exception as e:
			print("Failed to start audio automatically:", e)

	# Ensure output dir exists
	os.makedirs(OUTPUT_DIR, exist_ok=True)

	running = True
	while running:
		dt = clock.tick_busy_loop(fps) / 1000.0
		for ev in pygame.event.get():
			if ev.type == pygame.QUIT:
				running = False
			elif ev.type == pygame.KEYDOWN:
				key = ev.key
				uni = getattr(ev, 'unicode', '')
				if key == pygame.K_ESCAPE:
					running = False
				elif key == pygame.K_SPACE:
					# Toggle play/pause and control audio if available
					playing = not playing
					if playing:
						# resume or start audio
						if audio_enabled:
							try:
								if not audio_started:
									pygame.mixer.music.play(loops=-1)
									audio_started = True
									audio_start_time = time.time()
								else:
									pygame.mixer.music.unpause()
							except Exception as e:
								print("Audio unpause failed:", e)
						last_time = time.time()
					else:
						# pause audio if playing
						if audio_enabled and audio_started:
							try:
								pygame.mixer.music.pause()
							except Exception:
								pass
				# Accept arrow keys or literal '[' and ']' typed (use ev.unicode)
				elif (key == pygame.K_RIGHT) or (uni == ']'):
					if not playing:
						frame_index = (frame_index + 1) % max(1, len(frame_files))
						cur_frame = current_frame_surface(frame_index)
				elif (key == pygame.K_LEFT) or (uni == '['):
					if not playing:
						frame_index = (frame_index - 1) % max(1, len(frame_files))
						cur_frame = current_frame_surface(frame_index)
				elif ev.key == pygame.K_c:
					overlay.fill((0, 0, 0, 0))
				elif ev.key == pygame.K_s:
					# Save current combined frame
					name = f"frame_{frame_index:05d}_combined.png"
					path = os.path.join(OUTPUT_DIR, name)
					if save_combined(cur_frame, overlay, path):
						print("Saved:", path)
				elif ev.key == pygame.K_PLUS or ev.key == pygame.K_EQUALS:
					brush_radius = min(200, brush_radius + 1)
				elif ev.key == pygame.K_MINUS or ev.key == pygame.K_UNDERSCORE:
					brush_radius = max(1, brush_radius - 1)
				elif ev.key == pygame.K_COMMA:
					# volume down
					volume = max(0.0, volume - 0.1)
					if audio_enabled and audio_started:
						try:
							pygame.mixer.music.set_volume(0.0 if muted else volume)
						except Exception:
							pass
				elif ev.key == pygame.K_PERIOD:
					# volume up
					volume = min(1.0, volume + 0.1)
					if audio_enabled and audio_started:
						try:
							pygame.mixer.music.set_volume(0.0 if muted else volume)
						except Exception:
							pass
				elif ev.key == pygame.K_m:
					# mute toggle
					muted = not muted
					if audio_enabled and audio_started:
						try:
							pygame.mixer.music.set_volume(0.0 if muted else volume)
						except Exception:
							pass
			elif ev.type == pygame.MOUSEBUTTONDOWN:
				if ev.button == 1:
					drawing = True
				elif ev.button == 3:
					erasing = True
			elif ev.type == pygame.MOUSEBUTTONUP:
				if ev.button == 1:
					drawing = False
				elif ev.button == 3:
					erasing = False

		# Determine desired frame index
		if audio_enabled and audio_started and playing:
			# Prefer mixer position as master clock when available
			pos_ms = pygame.mixer.music.get_pos()
			if pos_ms is not None and pos_ms >= 0:
				elapsed = pos_ms / 1000.0
			else:
				# fallback to wall-clock relative to audio start
				if audio_start_time is not None:
					elapsed = time.time() - audio_start_time - audio_pause_acc
				else:
					elapsed = time.time() - start_time
			if frame_files:
				desired = int(elapsed * fps)
				if desired != frame_index:
					frame_index = desired % len(frame_files)
					cur_frame = current_frame_surface(frame_index)
		else:
			# No audio master — use wall-clock stepping
			if playing and frame_files:
				now = time.time()
				if now - last_time >= 1.0 / fps:
					frame_index += 1
					if frame_index >= len(frame_files):
						frame_index = 0
					cur_frame = current_frame_surface(frame_index)
					last_time = now

		# Handle drawing each frame
		mx, my = pygame.mouse.get_pos()
		if drawing and pygame.mouse.get_pressed()[0]:
			pygame.draw.circle(overlay, brush_color, (mx, my), brush_radius)
		if erasing and pygame.mouse.get_pressed()[2]:
			# Erase by drawing transparent circle; reuse surface where possible
			if erase_surf is None or erase_surf.get_width() != brush_radius * 2:
				erase_surf = pygame.Surface((brush_radius * 2, brush_radius * 2), pygame.SRCALPHA)
				erase_surf.fill((0, 0, 0, 0))
				pygame.draw.circle(erase_surf, (0, 0, 0, 0), (brush_radius, brush_radius), brush_radius)
			overlay.blit(erase_surf, (mx - brush_radius, my - brush_radius), special_flags=pygame.BLEND_RGBA_MIN)

		# Render
		screen.blit(cur_frame, (0, 0))
		screen.blit(overlay, (0, 0))

		# HUD with semi-transparent background for readability
		info = f"Frame {frame_index+1}/{max(1,len(frame_files))}  FPS={fps}  Brush={brush_radius}  Vol={'M' if muted else f'{volume:.2f}'}  Playing={'Yes' if playing else 'No'}"
		txt = font.render(info, True, (255, 255, 255))
		# draw translucent boxes behind text
		box = pygame.Surface((max(300, txt.get_width()+16), txt.get_height()+8), pygame.SRCALPHA)
		box.fill((0, 0, 0, 160))
		screen.blit(box, (4, 4))
		screen.blit(txt, (8, 8))
		# bottom instruction box
		box2 = pygame.Surface((instr_surf.get_width()+16, instr_surf.get_height()+8), pygame.SRCALPHA)
		box2.fill((0, 0, 0, 160))
		screen.blit(box2, (4, h - 28))
		screen.blit(instr_surf, (8, h - 24))

		pygame.display.flip()

if __name__ == "__main__":
	main()


