# Lantern Drift

Full-colour Python 3 neon wind-river arcade for **ElbowOS**.
Steer a paper lantern boat through gusts, collect floating wishes, pulse to stun shadow eels.

Featured: [x.com/ElbowOS](https://x.com/ElbowOS)

Reel (9:16 MP4): [Google Drive](https://drive.google.com/file/d/1iHdf1c_XMBk62gvgvyWMMrj1eADpCNOv/view?usp=drivesdk)

## Play

```bash
pip install -r requirements.txt
python3 lantern_drift.py --play
```

Controls: **A / D** or arrows to drift, **Space / W / Up** to pulse the lantern, **R** restart, **Esc** quit.

## Record a 15s 1080x1920 reel

```bash
ELBOWOS_RECORD=1 python3 lantern_drift.py --record
```

Writes `/home/workdir/artifacts/LANTERN_DRIFT_ElbowOS.mp4` (override with `ELBOWOS_MP4`).
