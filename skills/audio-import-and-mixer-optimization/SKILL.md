---
name: audio-import-and-mixer-optimization
description: "Audio import and mixer tuning for mobile: load type, compression, sample rate, force mono for 3D, mixer depth and effects, snapshots, DSP buffer. Use when audio memory is high, DSP CPU spikes, 3D sound plays one channel or SFX load stalls."
triggers: audio memory, audio import, load type, vorbis, aac, sample rate, force to mono, audio mixer, mixer snapshot, dsp buffer, audio cpu, streaming audio, bo nho am thanh, nen am thanh, am thanh 3d, mixer am thanh
---

# Audio import and mixer optimization

Source: official (Unity-Technologies/skills/optimize-audio, audio-setup-mixers), re-written. Pairs with `game-audio-system` and `sfx-variation-ducking`.

## Import matrix (mobile)
| Clip | Load type | Compression | Rate | Mono |
|---|---|---|---|---|
| Short SFX under ~200 KB | Decompress On Load | Vorbis (Android) / AAC (iOS) or ADPCM | 22050 | yes if 3D |
| Medium, occasional | Compressed In Memory | Vorbis / AAC | 22050-44100 | as needed |
| Music, long ambience, voice | Streaming + Load In Background | Vorbis / AAC | 44100 | no |
- Decompress On Load on a clip over ~1 MB bloats RAM; Streaming on a clip that plays many times at once adds disk pressure.
- Halving the sample rate halves PCM memory: report the estimated saving per clip.
- Keep sources as WAV: re-encoding an MP3 loses quality permanently.
- A 3D AudioSource (`spatialBlend` > 0) with a stereo clip plays unevenly: set Force To Mono on the importer and check rolloff.
- Vorbis quality 0.5-0.7 for SFX, higher for voice; check artifacts by ear.

## Mixer
- Keep group depth at most 3 (Master > SFX/Music/UI > optional sub-bus). Each level costs DSP every frame.
- Effects run even on silent groups: remove or bypass unused ones. SFX Reverb on a parent group is the most expensive built-in.
- Switch mix states with snapshots (menu, play, pause, ducking), not by toggling effects at runtime.
- Expose volume parameters per channel (Master, Music, SFX); map slider 0..1 to dB with log10 and floor at -80.
- DSP buffer: 256 only when latency matters; 512 general; 1024 saves CPU/battery. Below 256 costs CPU.

## Steps
1. Audit with an Editor script via MCP: clips with size, load type, format, rate, channels, 3D users. Write the result to a file, not the chat.
2. Apply importer changes in batches by folder (`AudioImporter`, `SaveAndReimport`); this is a bulk asset change, confirm scope first.
3. Audit mixers: group depth, effects list, snapshots, exposed params.
4. Verify: Profiler Audio module before/after (DSP load, memory), Console clean, listen to the top 5 changed clips. [ours] Never claim a gain without numbers.
