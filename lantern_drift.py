#!/usr/bin/env python3
"""Lantern Drift — neon wind-river arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/LANTERN_DRIFT_ElbowOS.mp4")
TITLE, HANDLE = "LANTERN DRIFT", "x.com/ElbowOS"

BG = (6, 16, 24)
DEEP = (8, 28, 38)
INK = (18, 48, 68)
CREAM = (255, 231, 194)
AMBER = (255, 179, 71)
VERM = (255, 72, 64)
JADE = (61, 255, 176)
TEAL = (40, 210, 220)
GOLD = (255, 214, 90)
WHITE = (252, 248, 240)
VIO = (150, 120, 255)
SHADOW = (28, 12, 48)


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        self.font_lg = pygame.font.SysFont("DejaVu Sans", 56, bold=True)
        self.font = pygame.font.SysFont("DejaVu Sans", 36, bold=True)
        self.font_sm = pygame.font.SysFont("DejaVu Sans", 26)
        self.clock = pygame.time.Clock()
        self.x, self.y = W * 0.5, 1480
        self.vx = self.score = self.combo = self.t = self.flash = 0
        self.pulse = 0
        self.gusts, self.wishes, self.eels, self.sparks, self.trail = [], [], [], [], []
        self.ripples = []
        self.stars = [[random.randint(0, W), random.randint(0, H),
                       random.uniform(0.6, 2.4), random.choice((JADE, AMBER, TEAL, CREAM))]
                      for _ in range(64)]
        self.reeds = [[random.randint(20, W - 20), random.randint(0, H),
                       random.uniform(40, 90), random.choice((-1, 1))]
                      for _ in range(18)]
        self.reset()

    def reset(self):
        self.lives = 3
        self.combo = 0
        self.x = W * 0.5
        self.vx = 0
        self.wish_cd = 10
        self.eel_cd = 22
        self.gust_cd = 14

    def burst(self, x, y, col, n=16):
        for _ in range(n):
            a = random.uniform(0, 6.2832)
            sp = random.uniform(2.5, 12)
            self.sparks.append([x, y, math.cos(a) * sp, math.sin(a) * sp, 18, col])

    def wind_at(self, y):
        p = self.t * 0.04 + y * 0.0035
        return math.sin(p) * 7.5 + math.sin(p * 0.41 + 1.2) * 4.0

    def spawn_wish(self):
        self.wishes.append([random.uniform(90, W - 90), -40, random.choice((AMBER, GOLD, CREAM)), False])

    def spawn_eel(self):
        side = random.choice((-1, 1))
        self.eels.append([W * 0.5 + side * random.uniform(80, 360), -70,
                          side * random.uniform(2.2, 5.5), 0.0])

    def spawn_gust(self):
        self.gusts.append([random.uniform(120, W - 120), -30, random.choice((-1, 1)), 90])

    def pulse_blast(self):
        if self.pulse > 8:
            return
        self.pulse = 22
        self.ripples.append([self.x, self.y, 20])
        for e in list(self.eels):
            if (e[0] - self.x) ** 2 + (e[1] - self.y) ** 2 < 170 ** 2:
                self.burst(e[0], e[1], JADE, 12)
                self.eels.remove(e)
                self.score += 15
                self.combo += 1
        for w in self.wishes:
            if not w[3] and (w[0] - self.x) ** 2 + (w[1] - self.y) ** 2 < 200 ** 2:
                w[3] = True
                self.score += 12 + self.combo * 3
                self.combo += 1
                self.burst(w[0], w[1], w[2], 14)

    def hit_check(self):
        for w in self.wishes:
            if w[3]:
                continue
            if (w[0] - self.x) ** 2 + (w[1] - self.y) ** 2 < 48 ** 2:
                w[3] = True
                self.combo += 1
                self.score += 10 + self.combo * 2
                self.burst(w[0], w[1], w[2], 16)
        for e in list(self.eels):
            if (e[0] - self.x) ** 2 + (e[1] - self.y) ** 2 < 46 ** 2:
                self.lives -= 1
                self.combo = 0
                self.flash = 10
                self.burst(self.x, self.y, VERM, 22)
                self.eels.remove(e)
                if self.lives <= 0:
                    self.score = max(0, self.score - 20)
                    self.reset()

    def autoplay(self):
        targets = [w for w in self.wishes if not w[3] and -10 < w[1] < self.y + 80]
        threats = [e for e in self.eels if abs(e[1] - self.y) < 260]
        want = self.x
        if targets:
            w = min(targets, key=lambda z: abs(z[1] - self.y) + abs(z[0] - self.x) * 0.35)
            want = w[0]
        for e in threats:
            if abs(want - e[0]) < 80:
                want += 140 if self.x >= e[0] else -140
        want = max(90, min(W - 90, want))
        err = want - self.x
        self.vx = max(-22, min(22, err * 0.22 + math.sin(self.t * 0.13) * 1.2))
        near_eel = any((e[0] - self.x) ** 2 + (e[1] - self.y) ** 2 < 150 ** 2 for e in self.eels)
        clustered = sum(1 for w in self.wishes if not w[3] and (w[0] - self.x) ** 2 + (w[1] - self.y) ** 2 < 190 ** 2)
        if (near_eel or clustered >= 2) and self.t % 18 == 0:
            self.pulse_blast()

    def tick(self):
        self.t += 1
        self.flash = max(0, self.flash - 1)
        self.pulse = max(0, self.pulse - 1)
        flow = 11 + min(7, self.t / 100)
        self.vx += self.wind_at(self.y) * 0.18
        for g in self.gusts:
            if abs(g[1] - self.y) < 70 and abs(g[0] - self.x) < g[3]:
                self.vx += g[2] * 1.6
        self.x = max(70, min(W - 70, self.x + self.vx))
        self.vx *= 0.86
        self.wish_cd -= 1
        self.eel_cd -= 1
        self.gust_cd -= 1
        if self.wish_cd <= 0:
            self.spawn_wish()
            self.wish_cd = max(12, 22 - self.t // 80)
        if self.eel_cd <= 0:
            self.spawn_eel()
            self.eel_cd = max(16, 28 - self.t // 70)
        if self.gust_cd <= 0:
            self.spawn_gust()
            self.gust_cd = max(18, 30 - self.t // 90)
        for w in self.wishes:
            w[1] += flow
            w[0] += math.sin(self.t * 0.08 + w[1] * 0.01) * 1.4
        for e in self.eels:
            e[1] += flow * 0.92
            e[0] += e[2] + math.sin(self.t * 0.12 + e[1] * 0.02) * 2.4
            e[3] += 0.18
            if e[0] < 40 or e[0] > W - 40:
                e[2] *= -1
        for g in self.gusts:
            g[1] += flow * 0.7
        self.wishes = [w for w in self.wishes if w[1] < H + 40]
        self.eels = [e for e in self.eels if e[1] < H + 50]
        self.gusts = [g for g in self.gusts if g[1] < H + 40]
        self.hit_check()
        self.trail.append([self.x, self.y + 18, 14])
        self.trail = self.trail[-30:]
        for tr in self.trail:
            tr[2] -= 0.4
        for s in self.sparks:
            s[0] += s[2]
            s[1] += s[3] + flow * 0.12
            s[4] -= 1
        self.sparks = [s for s in self.sparks if s[4] > 0]
        for r in self.ripples:
            r[2] += 9
        self.ripples = [r for r in self.ripples if r[2] < 240]
        for st in self.stars:
            st[1] += st[2] + flow * 0.18
            if st[1] > H + 4:
                st[1] = -4
                st[0] = random.randint(0, W)
        for rd in self.reeds:
            rd[1] += flow * 0.55
            if rd[1] > H + 80:
                rd[1] = -80
                rd[0] = random.randint(20, W - 20)

    def draw(self, surf):
        surf.fill(BG)
        for i in range(18):
            y0 = (i * 120 + int(self.t * 4)) % (H + 120) - 60
            pygame.draw.ellipse(surf, INK, (40, y0, W - 80, 70), 0)
        for st in self.stars:
            pygame.draw.circle(surf, st[3], (int(st[0]), int(st[1])), 2)
        for rd in self.reeds:
            sway = math.sin(self.t * 0.07 + rd[0]) * 16 * rd[3]
            pygame.draw.line(surf, (20, 70, 62), (rd[0], rd[1] + rd[2]),
                             (rd[0] + sway, rd[1]), 4)
        for g in self.gusts:
            col = (40, 90, 110)
            pygame.draw.ellipse(surf, col, (int(g[0] - g[3]), int(g[1] - 16), int(g[3] * 2), 32), 2)
            pygame.draw.line(surf, TEAL, (g[0] - 30 * g[2], g[1]), (g[0] + 40 * g[2], g[1]), 3)
        for w in self.wishes:
            if w[3]:
                continue
            wx, wy = int(w[0]), int(w[1])
            glow = 10 + int(4 * math.sin(self.t * 0.2 + wx))
            pygame.draw.circle(surf, w[2], (wx, wy), glow)
            pygame.draw.circle(surf, WHITE, (wx, wy - 4), 5)
            pygame.draw.polygon(surf, VERM, [(wx, wy - glow - 8), (wx - 5, wy - 2), (wx + 5, wy - 2)])
        for e in self.eels:
            ex, ey = int(e[0]), int(e[1])
            body = []
            for k in range(8):
                body.append((ex + int(math.sin(e[3] + k * 0.7) * 10) - k * 6,
                             ey + int(math.cos(e[3] * 0.8 + k) * 4) + k * 3))
            if len(body) > 1:
                pygame.draw.lines(surf, SHADOW, False, body, 10)
                pygame.draw.lines(surf, VIO, False, body, 4)
            pygame.draw.circle(surf, VERM, (ex, ey), 7)
        for tr in self.trail:
            if tr[2] > 0:
                pygame.draw.circle(surf, TEAL, (int(tr[0]), int(tr[1])), max(2, int(tr[2])))
        for r in self.ripples:
            pygame.draw.circle(surf, JADE, (int(r[0]), int(r[1])), int(r[2]), 2)
        bx, by = int(self.x), int(self.y)
        lean = self.vx * 1.4
        hull = [(bx - 38 + lean, by + 16), (bx + 38 + lean, by + 16),
                (bx + 22 + lean, by + 34), (bx - 22 + lean, by + 34)]
        pygame.draw.polygon(surf, (70, 42, 28), hull)
        pygame.draw.polygon(surf, GOLD, hull, 2)
        pygame.draw.polygon(surf, CREAM, [(bx + lean * 0.3, by - 54),
                                          (bx - 20, by + 10), (bx + 20, by + 10)])
        pygame.draw.circle(surf, AMBER, (bx + int(lean * 0.2), by - 28), 16)
        pygame.draw.circle(surf, GOLD, (bx + int(lean * 0.2), by - 30), 8)
        pygame.draw.circle(surf, WHITE, (bx + int(lean * 0.2) - 3, by - 33), 3)
        if self.pulse:
            pygame.draw.circle(surf, JADE, (bx, by), 12 + (22 - self.pulse), 2)
        for s in self.sparks:
            pygame.draw.circle(surf, s[5], (int(s[0]), int(s[1])), max(2, s[4] // 4))
        if self.flash:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((255, 50, 70, 55))
            surf.blit(ov, (0, 0))
        title = self.font_lg.render(TITLE, True, GOLD)
        surf.blit(title, title.get_rect(center=(W // 2, 84)))
        sub = self.font_sm.render(HANDLE, True, TEAL)
        surf.blit(sub, sub.get_rect(center=(W // 2, 146)))
        sc = self.font.render(f"SCORE  {self.score}", True, WHITE)
        lv = self.font.render(f"LIVES  {'\u25c6' * max(0, self.lives)}", True, VERM)
        cb = self.font_sm.render(f"COMBO  x{self.combo}", True, JADE)
        surf.blit(sc, sc.get_rect(center=(W // 2, H - 168)))
        surf.blit(lv, lv.get_rect(center=(W // 2, H - 108)))
        surf.blit(cb, cb.get_rect(center=(W // 2, H - 58)))

    def play_interactive(self):
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                    self.reset()
                    self.score = 0
                elif ev.type == pygame.KEYDOWN and ev.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    self.pulse_blast()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vx = -20
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vx = 20
            self.tick()
            self.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def record(self):
        frames = FPS * SECS
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart",
            OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        canvas = pygame.Surface((W, H))
        try:
            for i in range(frames):
                self.autoplay()
                self.tick()
                self.draw(canvas)
                proc.stdin.write(pygame.image.tostring(canvas, "RGB"))
                if i % 30 == 0:
                    print(f"frame {i}/{frames}", flush=True)
        finally:
            proc.stdin.close()
            err = proc.stderr.read().decode("utf-8", "ignore")
            rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        print("wrote", OUT)
        pygame.quit()


def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()


if __name__ == "__main__":
    main()
