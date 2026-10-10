import math
import random
import time
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath, QFont, QRadialGradient, QLinearGradient
)

class Particle:
    """Floating particle for visual effects (hearts, Zzz, stars)."""
    def __init__(self, x, y, p_type="heart", text=None):
        self.x = x
        self.y = y
        self.p_type = p_type
        self.text = text or ("❤️" if p_type == "heart" else "Z")
        self.life = 1.0  # 1.0 -> 0.0
        self.decay = random.uniform(0.015, 0.03)
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-1.8, -1.0)
        self.scale = random.uniform(0.8, 1.2)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay
        return self.life > 0

    def draw(self, painter: QPainter):
        painter.save()
        painter.setOpacity(max(0.0, self.life))
        font = QFont("Sans-Serif", int(14 * self.scale), QFont.Weight.Bold)
        painter.setFont(font)
        if self.p_type == "heart":
            painter.setPen(QPen(QColor(255, 75, 120)))
            painter.drawText(QPointF(self.x, self.y), "♥")
        elif self.p_type == "zzz":
            painter.setPen(QPen(QColor(130, 160, 240)))
            painter.drawText(QPointF(self.x, self.y), "Z")
        elif self.p_type == "sparkle":
            painter.setPen(QPen(QColor(255, 215, 0)))
            painter.drawText(QPointF(self.x, self.y), "✦")
        painter.restore()


class AvatarCharacter:
    """
    Procedural 2D animated avatar engine.
    Renders an expressive, reactive anime-style desktop companion with:
    - Smooth squash & stretch physics
    - Eye cursor tracking
    - Blinking & facial expressions
    - Tail wagging physics
    - Walk cycle, dangling, falling, sleeping, and dance animations
    - Speech bubbles and emotion particles
    """
    def __init__(self, size=150):
        self.size = size
        self.half_size = size / 2.0
        self.time = 0.0

        # State
        self.state = "idle"  # idle, walk, sleep, dragged, falling, happy
        self.facing_right = True

        # Animation parameters
        self.walk_phase = 0.0
        self.tail_phase = 0.0
        self.blink_timer = 0.0
        self.is_blinking = False

        # Physics squish
        self.squish_x = 1.0
        self.squish_y = 1.0

        # Eye tracking coordinates (normalized -1.0 to 1.0)
        self.target_eye_x = 0.0
        self.target_eye_y = 0.0
        self.curr_eye_x = 0.0
        self.curr_eye_y = 0.0

        # Speech bubble
        self.speech_text = None
        self.speech_timer = 0.0

        # Particles
        self.particles = []

        # Color Theme: Warm Golden/Caramel Fox-Cat
        self.fur_main = QColor(255, 160, 80)
        self.fur_dark = QColor(230, 130, 50)
        self.fur_belly = QColor(255, 245, 230)
        self.fur_inner_ear = QColor(255, 175, 185)
        self.cheek_color = QColor(255, 110, 140, 160)
        self.eye_color = QColor(45, 45, 55)

        self.last_quote_time = time.time()
        self.on_speech_requested = None
        self.idle_quotes = [
            "Hi friend! (=^･ω･^=)",
            "What are we working on?",
            "Remember to hydrate! 💧",
            "Stretch your shoulders! ✨",
            "I'm keeping you company!",
            "Purr-fect day for coding!",
            "Need a quick break?",
        ]

    def set_speech(self, text, duration=4.0, title=None, actions=None):
        self.speech_text = text
        self.speech_timer = duration
        if self.on_speech_requested:
            self.on_speech_requested(text, duration=duration, title=title, actions=actions)

    def add_particle(self, p_type="heart"):
        # Emit near top of avatar
        px = self.half_size + random.uniform(-20, 20)
        py = self.half_size - 30 + random.uniform(-10, 10)
        self.particles.append(Particle(px, py, p_type))

    def update(self, dt, mouse_rel_pos=None):
        self.time += dt
        self.tail_phase += dt * (5.0 if self.state == "happy" else 3.0)

        # Update speech timer
        if self.speech_timer > 0:
            self.speech_timer -= dt
            if self.speech_timer <= 0:
                self.speech_text = None



        # Smooth squish recovery
        self.squish_x += (1.0 - self.squish_x) * min(1.0, dt * 10.0)
        self.squish_y += (1.0 - self.squish_y) * min(1.0, dt * 10.0)

        # Blinking logic
        self.blink_timer -= dt
        if self.blink_timer <= 0:
            if self.is_blinking:
                self.is_blinking = False
                self.blink_timer = random.uniform(2.5, 6.0)
            else:
                self.is_blinking = True
                self.blink_timer = 0.15  # blink duration

        # Sleeping particles
        if self.state == "sleep" and random.random() < 0.04:
            self.add_particle("zzz")

        # Happy sparkles
        if self.state == "happy" and random.random() < 0.15:
            self.add_particle("heart" if random.random() < 0.6 else "sparkle")

        # Eye tracking calculation
        if mouse_rel_pos and self.state not in ("sleep", "dragged"):
            mx, my = mouse_rel_pos
            # Clamp to range -1.0 to 1.0
            dist = math.hypot(mx, my) + 1e-5
            max_dist = 400.0
            factor = min(1.0, dist / max_dist)
            self.target_eye_x = (mx / dist) * factor
            self.target_eye_y = (my / dist) * factor
        else:
            self.target_eye_x = 0.0
            self.target_eye_y = 0.0

        # Smooth eye interpolation
        self.curr_eye_x += (self.target_eye_x - self.curr_eye_x) * min(1.0, dt * 8.0)
        self.curr_eye_y += (self.target_eye_y - self.curr_eye_y) * min(1.0, dt * 8.0)

        # Walk animation phase
        if self.state == "walk":
            self.walk_phase += dt * 10.0

        # Update particles
        self.particles = [p for p in self.particles if p.update()]

    def trigger_landing_squish(self):
        """Squash on landing."""
        self.squish_x = 1.35
        self.squish_y = 0.65

    def draw(self, painter: QPainter):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        # Draw particles first (behind or around)
        for p in self.particles:
            p.draw(painter)

        cx = self.half_size
        cy = self.half_size + 15

        # Base breathing / idle bob
        breathe = math.sin(self.time * 2.5) * 2.0 if self.state != "sleep" else math.sin(self.time * 1.5) * 1.0
        walk_bob = math.sin(self.walk_phase * 2.0) * 3.0 if self.state == "walk" else 0.0
        dance_bob = abs(math.sin(self.time * 12.0)) * 12.0 if self.state == "happy" else 0.0

        center_y = cy - breathe - walk_bob - dance_bob

        # Apply squish transform centered around base
        painter.translate(cx, center_y + 35)
        painter.scale(self.squish_x, self.squish_y)
        painter.translate(-cx, -(center_y + 35))

        # Face orientation flip if walking left
        if not self.facing_right and self.state != "dragged":
            painter.translate(cx, 0)
            painter.scale(-1, 1)
            painter.translate(-cx, 0)

        # 1. Shadow underneath
        if self.state not in ("dragged", "falling"):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 40))
            shadow_w = 70 * self.squish_x
            shadow_h = 16 * self.squish_y
            painter.drawEllipse(QPointF(cx, cy + 42), shadow_w / 2, shadow_h / 2)

        # 2. Tail
        self._draw_tail(painter, cx, center_y)

        # 3. Body
        self._draw_body(painter, cx, center_y)

        # 4. Ears
        self._draw_ears(painter, cx, center_y)

        # 5. Face (Eyes, Nose, Cheeks, Mouth)
        self._draw_face(painter, cx, center_y)

        # 6. Paws / Legs
        self._draw_paws(painter, cx, center_y)

        painter.restore()

    def _draw_tail(self, painter: QPainter, cx, cy):
        painter.save()
        tail_angle = math.sin(self.tail_phase) * 18.0
        if self.state == "dragged":
            tail_angle = math.sin(self.time * 14.0) * 25.0

        # Anchor at back left of body
        base_x = cx - 30
        base_y = cy + 18

        tail_path = QPainterPath()
        tail_path.moveTo(base_x, base_y)
        tip_x = base_x - 30 + math.cos(math.radians(tail_angle)) * 10
        tip_y = base_y - 35 + math.sin(math.radians(tail_angle)) * 18
        ctrl_x = base_x - 45
        ctrl_y = base_y + 5

        tail_path.quadTo(ctrl_x, ctrl_y, tip_x, tip_y)

        pen = QPen(self.fur_main, 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(tail_path)

        # Tail tip white accent
        tip_pen = QPen(self.fur_belly, 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(tip_pen)
        painter.drawPoint(QPointF(tip_x, tip_y))
        painter.restore()

    def _draw_ears(self, painter: QPainter, cx, cy):
        ear_twitch = math.sin(self.time * 4.0) * 2.0 if random.random() < 0.05 else 0.0

        for side, is_right in [(-1, False), (1, True)]:
            painter.save()
            ear_x = cx + side * 28
            ear_y = cy - 25

            # Outer ear
            path = QPainterPath()
            path.moveTo(ear_x - 14, ear_y + 5)
            # Tip
            tip_x = ear_x + side * 8 + (ear_twitch if is_right else 0)
            tip_y = ear_y - 28
            path.lineTo(tip_x, tip_y)
            path.lineTo(ear_x + 14, ear_y + 5)
            path.closeSubpath()

            painter.setPen(QPen(self.fur_dark, 2))
            painter.setBrush(QBrush(self.fur_main))
            painter.drawPath(path)

            # Inner ear
            inner = QPainterPath()
            inner.moveTo(ear_x - 8, ear_y + 2)
            inner.lineTo(tip_x, tip_y + 8)
            inner.lineTo(ear_x + 8, ear_y + 2)
            inner.closeSubpath()

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(self.fur_inner_ear))
            painter.drawPath(inner)
            painter.restore()

    def _draw_body(self, painter: QPainter, cx, cy):
        painter.save()
        painter.setPen(QPen(self.fur_dark, 2))

        # Main round fluffy body
        grad = QLinearGradient(cx, cy - 35, cx, cy + 35)
        grad.setColorAt(0.0, self.fur_main)
        grad.setColorAt(1.0, self.fur_dark)
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(QPointF(cx, cy), 42, 38)

        # Cream belly patch
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.fur_belly))
        painter.drawEllipse(QPointF(cx + 4, cy + 12), 26, 22)
        painter.restore()

    def _draw_face(self, painter: QPainter, cx, cy):
        # Cheeks
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.cheek_color))
        painter.drawEllipse(QPointF(cx - 25, cy + 3), 7, 5)
        painter.drawEllipse(QPointF(cx + 25, cy + 3), 7, 5)
        painter.restore()

        # Sleeping face
        if self.state == "sleep":
            self._draw_closed_eyes(painter, cx, cy)
            self._draw_sleeping_mouth(painter, cx, cy)
            return

        # Happy / Closed eyes when ecstatic
        if self.state == "happy" or self.is_blinking:
            self._draw_happy_eyes(painter, cx, cy)
        else:
            self._draw_open_eyes(painter, cx, cy)

        # Nose & Mouth
        self._draw_mouth_nose(painter, cx, cy)

    def _draw_open_eyes(self, painter: QPainter, cx, cy):
        eye_spacing = 18
        eye_y = cy - 6
        eye_w = 11
        eye_h = 13

        for side in (-1, 1):
            ex = cx + side * eye_spacing
            ey = eye_y

            # White sclera
            painter.setPen(QPen(self.fur_dark, 1.5))
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(QPointF(ex, ey), eye_w, eye_h)

            # Iris / Pupil tracking cursor
            pupil_ox = self.curr_eye_x * 4.0
            pupil_oy = self.curr_eye_y * 4.0
            px = ex + pupil_ox
            py = ey + pupil_oy

            # Iris
            painter.setPen(Qt.PenStyle.NoPen)
            iris_grad = QRadialGradient(px, py, 7)
            iris_grad.setColorAt(0.0, QColor(20, 20, 30))
            iris_grad.setColorAt(0.8, QColor(70, 45, 120))
            iris_grad.setColorAt(1.0, QColor(30, 20, 50))
            painter.setBrush(QBrush(iris_grad))
            painter.drawEllipse(QPointF(px, py), 7, 8)

            # Shiny eye highlight reflection (Anime style shine)
            painter.setBrush(QColor(255, 255, 255, 240))
            painter.drawEllipse(QPointF(px - 2.5, py - 3), 2.8, 3.2)
            painter.drawEllipse(QPointF(px + 2, py + 2.5), 1.5, 1.5)

    def _draw_happy_eyes(self, painter: QPainter, cx, cy):
        eye_spacing = 18
        eye_y = cy - 5
        pen = QPen(self.eye_color, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        for side in (-1, 1):
            ex = cx + side * eye_spacing
            path = QPainterPath()
            path.moveTo(ex - 7, eye_y + 2)
            path.quadTo(ex, eye_y - 6, ex + 7, eye_y + 2)
            painter.drawPath(path)

    def _draw_closed_eyes(self, painter: QPainter, cx, cy):
        eye_spacing = 18
        eye_y = cy - 4
        pen = QPen(self.eye_color, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        for side in (-1, 1):
            ex = cx + side * eye_spacing
            path = QPainterPath()
            path.moveTo(ex - 7, eye_y)
            path.quadTo(ex, eye_y + 4, ex + 7, eye_y)
            painter.drawPath(path)

    def _draw_mouth_nose(self, painter: QPainter, cx, cy):
        # Little cute nose
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(245, 120, 140))
        painter.drawEllipse(QPointF(cx, cy + 2), 3, 2)

        # Mouth (:3 cat smile)
        painter.setPen(QPen(self.eye_color, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if self.state == "happy":
            # Open happy smiling mouth :D
            open_mouth = QPainterPath()
            open_mouth.moveTo(cx - 6, cy + 7)
            open_mouth.quadTo(cx, cy + 16, cx + 6, cy + 7)
            open_mouth.closeSubpath()
            painter.setBrush(QColor(230, 80, 100))
            painter.drawPath(open_mouth)
        else:
            # Cute :3 curves
            m1 = QPainterPath()
            m1.moveTo(cx - 6, cy + 6)
            m1.quadTo(cx - 3, cy + 9, cx, cy + 6)
            painter.drawPath(m1)

            m2 = QPainterPath()
            m2.moveTo(cx, cy + 6)
            m2.quadTo(cx + 3, cy + 9, cx + 6, cy + 6)
            painter.drawPath(m2)

        # Whiskers
        painter.setPen(QPen(self.fur_dark, 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for dy in (-2, 3):
            # Left whiskers
            painter.drawLine(QPointF(cx - 28, cy + dy), QPointF(cx - 42, cy + dy * 1.5))
            # Right whiskers
            painter.drawLine(QPointF(cx + 28, cy + dy), QPointF(cx + 42, cy + dy * 1.5))

    def _draw_sleeping_mouth(self, painter: QPainter, cx, cy):
        # Cute bubble or tiny o mouth
        painter.setPen(QPen(self.eye_color, 1.5))
        painter.setBrush(QColor(255, 200, 210))
        painter.drawEllipse(QPointF(cx, cy + 7), 3, 3)

    def _draw_paws(self, painter: QPainter, cx, cy):
        painter.save()
        painter.setPen(QPen(self.fur_dark, 1.5))
        painter.setBrush(QBrush(self.fur_belly))

        if self.state == "walk":
            # Stepping walk cycle
            step1 = math.sin(self.walk_phase) * 6.0
            step2 = math.cos(self.walk_phase) * 6.0
            painter.drawEllipse(QPointF(cx - 16 + step1, cy + 34), 8, 6)
            painter.drawEllipse(QPointF(cx + 16 - step2, cy + 34), 8, 6)
        elif self.state == "dragged":
            # Dangling paws
            flail = math.sin(self.time * 15.0) * 4.0
            painter.drawEllipse(QPointF(cx - 18, cy + 38 + flail), 7, 9)
            painter.drawEllipse(QPointF(cx + 18, cy + 38 - flail), 7, 9)
        elif self.state == "falling":
            # Upward flailing paws
            painter.drawEllipse(QPointF(cx - 24, cy + 18), 8, 7)
            painter.drawEllipse(QPointF(cx + 24, cy + 18), 8, 7)
        else:
            # Cute resting paws in front
            painter.drawEllipse(QPointF(cx - 15, cy + 32), 9, 6)
            painter.drawEllipse(QPointF(cx + 15, cy + 32), 9, 6)

        painter.restore()

    def _draw_speech_bubble(self, painter: QPainter, bubble_center_x, bubble_bottom_y):
        painter.save()
        font = QFont("Sans-Serif", 11, QFont.Weight.Medium)
        painter.setFont(font)

        metrics = painter.fontMetrics()
        text_w = metrics.horizontalAdvance(self.speech_text) + 24
        text_h = metrics.height() + 14

        bx = bubble_center_x - text_w / 2
        by = bubble_bottom_y - text_h

        # Bubble polygon with tail pointing down to avatar
        bubble_rect = QRectF(bx, by, text_w, text_h)
        path = QPainterPath()
        path.addRoundedRect(bubble_rect, 12, 12)

        # Small triangle pointer at bottom
        tail_x = bubble_center_x
        tail_path = QPainterPath()
        tail_path.moveTo(tail_x - 6, by + text_h)
        tail_path.lineTo(tail_x, by + text_h + 8)
        tail_path.lineTo(tail_x + 6, by + text_h)
        tail_path.closeSubpath()
        path = path.united(tail_path)

        # Bubble Shadow & Body
        painter.setPen(QPen(QColor(220, 220, 230), 1.5))
        painter.setBrush(QColor(255, 255, 255, 245))
        painter.drawPath(path)

        # Text
        painter.setPen(QColor(40, 40, 50))
        painter.drawText(bubble_rect, Qt.AlignmentFlag.AlignCenter, self.speech_text)
        painter.restore()
