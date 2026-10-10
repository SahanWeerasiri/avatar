import random
import time
from logger import debug_log

class BehaviorManager:
    """
    Autonomous state controller for the 2D desktop avatar.
    Lifecycle rules:
    - Default state: Sleep quietly in the bottom-left corner so as not to distract during work.
    - On User Interaction (clicks/pets): Wakes up and stays awake for an interactive period.
      When idle for 20s after interaction, walks back to the bottom-left corner and sleeps.
    - On Reminder: Wakes up, stands idle so user can interact and click buttons.
      Keeps reminder open until input is given, then walks back to the bottom-left corner and sleeps.
    """
    def __init__(self, character):
        self.character = character
        self.walk_speed = 80.0  # px/s
        self.direction = 1       # 1 = right, -1 = left

        # Modes:
        # "sleeping_corner": asleep in bottom-left corner
        # "active": awake and interacting with user
        # "waiting_reminder": awake & idle waiting for user response on reminder
        # "returning_to_corner": walking to bottom-left corner to sleep
        self.mode = "returning_to_corner"
        self.awake_time_left = 0.0
        self.state_time_left = 3.0

        # Start by walking to bottom-left corner to sleep
        self.character.state = "walk"
        self.character.facing_right = False
        self.direction = -1
        debug_log("BEHAVIOR", "BehaviorManager initialized. Starting in mode='returning_to_corner' towards bottom-left corner")

    def wake_up(self, duration=20.0, reason="user"):
        """Wake up avatar due to user click or explicit action."""
        prev_mode = self.mode
        self.mode = "active"
        self.awake_time_left = duration
        self.character.state = "happy" if reason == "user" else "idle"
        self.state_time_left = 3.0
        debug_log("BEHAVIOR", f"wake_up: mode '{prev_mode}' -> 'active' (reason='{reason}', duration={duration:.1f}s, character.state='{self.character.state}')")

    def wake_up_for_reminder(self):
        """Wake up avatar for a scheduled reminder."""
        prev_mode = self.mode
        self.mode = "waiting_reminder"
        self.character.state = "idle"
        self.character.facing_right = True
        self.state_time_left = 999999
        debug_log("BEHAVIOR", f"wake_up_for_reminder: mode '{prev_mode}' -> 'waiting_reminder' (standing idle for user interaction)")

    def on_reminder_dismissed(self):
        """User clicked an action on reminder bubble; return to corner to sleep."""
        prev_mode = self.mode
        self.mode = "returning_to_corner"
        self.character.state = "walk"
        self.character.facing_right = False
        self.direction = -1
        debug_log("BEHAVIOR", f"on_reminder_dismissed: mode '{prev_mode}' -> 'returning_to_corner' (walking left to sleep in corner)")

    def send_to_sleep(self):
        """Immediately trigger return to corner and sleep."""
        prev_mode = self.mode
        self.mode = "returning_to_corner"
        self.character.state = "walk"
        self.character.facing_right = False
        self.direction = -1
        debug_log("BEHAVIOR", f"send_to_sleep: mode '{prev_mode}' -> 'returning_to_corner' (walking left to sleep in corner)")

    def set_state(self, new_state, duration=None, *args, **kwargs):
        """Compatibility method for setting character states safely."""
        old_state = self.character.state
        self.character.state = new_state
        if new_state in ("idle", "walk", "happy"):
            self.mode = "active"
            self.awake_time_left = duration or 20.0
            self.state_time_left = duration or 4.0
        elif new_state == "sleep":
            self.mode = "sleeping_corner"
        elif new_state in ("dragged", "falling"):
            self.mode = "active"
            self.awake_time_left = 30.0
        debug_log("BEHAVIOR", f"set_state: character.state '{old_state}' -> '{new_state}', mode -> '{self.mode}'")

    def update(self, dt, current_x, min_x, max_x):
        # Dragging or falling bypasses behavior updates
        if self.character.state in ("dragged", "falling"):
            return 0.0

        corner_target_x = min_x + 25.0

        # MODE 1: Asleep in corner
        if self.mode == "sleeping_corner":
            self.character.state = "sleep"
            return 0.0

        # MODE 2: Returning to bottom-left corner to sleep
        elif self.mode == "returning_to_corner":
            self.character.state = "walk"
            self.direction = -1
            self.character.facing_right = False

            dx = -self.walk_speed * dt
            next_x = current_x + dx

            if next_x <= corner_target_x:
                # Arrived at bottom-left corner!
                debug_log("BEHAVIOR", f"Arrived at bottom-left corner (x={next_x:.1f} <= target={corner_target_x:.1f}). Going to sleep 💤")
                self.mode = "sleeping_corner"
                self.character.state = "sleep"
                return float(corner_target_x - current_x)

            return dx

        # MODE 3: Waiting for user input on a reminder
        elif self.mode == "waiting_reminder":
            # Stay idle and stationary so user can easily read and click buttons
            self.character.state = "idle"
            return 0.0

        # MODE 4: Active interaction mode (awake after user clicked/petted)
        elif self.mode == "active":
            self.awake_time_left -= dt
            if self.awake_time_left <= 0:
                # User stopped interacting; walk back to corner to sleep
                debug_log("BEHAVIOR", "Interaction timeout expired. Sending avatar back to corner to sleep.")
                self.send_to_sleep()
                return 0.0

            # Alternate naturally between idle and short walks
            self.state_time_left -= dt
            if self.state_time_left <= 0:
                self._pick_active_state(current_x, min_x, max_x)

            # Move if walking
            if self.character.state == "walk":
                dx = self.direction * self.walk_speed * dt
                next_x = current_x + dx
                if next_x <= min_x + 15:
                    debug_log("BEHAVIOR", "Walk boundary left reached; turning right")
                    self.direction = 1
                    self.character.facing_right = True
                    dx = abs(dx)
                elif next_x >= min_x + 350:  # Stay around the left side area
                    debug_log("BEHAVIOR", "Walk boundary right reached; turning left")
                    self.direction = -1
                    self.character.facing_right = False
                    dx = -abs(dx)
                return dx

            return 0.0

        return 0.0

    def _pick_active_state(self, current_x, min_x, max_x):
        if self.character.state == "walk":
            self.character.state = "idle"
            self.state_time_left = random.uniform(3.0, 6.0)
            debug_log("BEHAVIOR", f"Transitioned to idle for {self.state_time_left:.1f}s")
        else:
            self.character.state = "walk"
            self.state_time_left = random.uniform(4.0, 8.0)
            if current_x <= min_x + 60:
                self.direction = 1
            else:
                self.direction = random.choice([-1, 1])
            self.character.facing_right = (self.direction > 0)
            dir_str = "right" if self.direction > 0 else "left"
            debug_log("BEHAVIOR", f"Transitioned to walk {dir_str} for {self.state_time_left:.1f}s")
