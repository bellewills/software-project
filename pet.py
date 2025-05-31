from enum import Enum
import paho.mqtt.client as mqtt
import json
import os
import time
import threading
import random
from datetime import datetime

# ----- PET STATE MACHINE -----

class State(Enum):
    HAPPY = "Happy"
    HUNGRY = "Hungry"
    LONELY = "Lonely"
    SAD = "Sad"
    SCARED = "Scared"
    SICK = "Sick"
    DEAD = "Dead"

# Save/load setup
SAVE_FILE = "pet_data.json"
HIDE_ROOMS = ["living", "bedroom", "bathroom", "front"]
hide_seek_active = False
game_feedback_msg = ""

# Save current pet state
def save_pet(pet):
    with open(SAVE_FILE, 'w') as f:
        json.dump({"name": pet.name, "bg_theme": pet.bg_theme}, f)

# Load saved pet or make new one
def load_pet():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                pet = Pet(data.get("name", "Your pet"))
                pet.bg_theme = data.get("bg_theme", "city")
                return pet
        except Exception:
            pass
    return Pet("Your pet")

# --- PET CLASS LOGIC ---
class Pet:
    def __init__(self, name="Your pet"):
        self.name = name
        self.state = State.HAPPY
        self.hunger_level = 0
        self.hungry_duration = 0
        self.attention_level = 100
        self.temperature = 22.0
        self.scared_level = 0
        self.sickness_level = 0
        self.sick_duration = 0
        self.created_time = time.time()
        self.last_hunger_update = time.time()
        self.last_hint = ""
        self.last_pet_time = time.time()
        self.hidden_room = None
        self.bg_theme = "city"  # default background theme

    #Choose name 
    def rename(self, new_name):
        self.name = new_name
        save_pet(self)

    # Choose Background (BG)
    def set_theme(self, theme):
        self.bg_theme = theme
        save_pet(self)

    # Feed pet
    def feed(self):
        self.hunger_level = max(0, self.hunger_level - 10)
        self.last_hunger_update = time.time()
        self.hungry_duration = 0
        if self.state == State.SICK:
            self.sickness_level = max(0, self.sickness_level - 20)
            self.sick_duration = 0
            print("🩺 Fed while sick — sickness reduced!")

    # Pet or interact with it
    def interact(self):
        self.attention_level = min(100, self.attention_level + 10)
        self.last_pet_time = time.time()
        if self.state == State.SCARED:
            self.scared_level = 0
        if self.state == State.SICK:
            self.sickness_level = max(0, self.sickness_level - 10)
            self.sick_duration = 0
            print("🩺 Pet interaction while sick — sickness reduced!")

    # Check temp – if bad, increase sickness
    def check_temperature(self):
        if self.temperature < 15 or self.temperature > 30:
            self.sickness_level += 30

    # Add to scared if noise - Didnt get to add in microphone to IOT house to scare the pet, but was able to send mock data to test
    def hear_noise(self):
        self.scared_level += 5

    # Give medicine
    def heal(self):
        if self.state == State.SICK:
            self.sickness_level = 0
            self.sick_duration = 0
            self.state = State.HAPPY

    # This is the main loop that checks everything and updates mood
    def update_state(self):
        if self.state == State.DEAD:
            print("Pet is dead. update_state() skipped.")
            return
        now = time.time()
        # Hunger timer
        if now - self.created_time > 60 and now - self.last_hunger_update > 10:
            self.hunger_level += 10
            self.hunger_level = min(self.hunger_level, 100)
            self.last_hunger_update = now
        new_state = self.state
        if self.state == State.SICK: # Handle sickness logic
            if self.hunger_level <= 50 and self.sickness_level <= 40:
                print("💊 Pet recovering, delaying sickness progression.")
                return
            if self.sickness_level > 50: 
                self.sick_duration += 1
                print(f"Sick duration: {self.sick_duration}")
                if self.sick_duration > 5:
                    new_state = State.DEAD
                    print("💀 Pet has died from prolonged sickness.")
                    self.state = new_state
                    return
            else:
                if self.hungry_duration == 0:
                    print("🤷 Pet recovered — sickness dropped.")
                    self.sick_duration = 0
                    new_state = State.HAPPY
        elif self.sickness_level > 50: # Become sick if too sick
            new_state = State.SICK
            self.sick_duration = 0
            print("⚠️ Pet became sick (sickness_level > 50).")
        elif self.hunger_level > 70 and self.state not in [State.SICK, State.DEAD]: # Handles hunger → sickness
            self.hungry_duration += 1
            print(f"[HUNGRY] hunger: {self.hunger_level}, duration: {self.hungry_duration}")
            new_state = State.HUNGRY
        if self.hungry_duration >= 12:
            new_state = State.SICK
            self.sick_duration = 0
            self.hungry_duration = 0
            self.sickness_level = 60
            print("⚠️ Pet became sick due to prolonged hunger.")
        elif self.hunger_level <= 70:
            self.hungry_duration = 0
        if self.state == State.HUNGRY and self.hunger_level <= 30:
            print("🍖 Pet is no longer hungry.")
            new_state = State.HAPPY
        if new_state not in [State.DEAD, State.SICK, State.SCARED, State.LONELY, State.HUNGRY]: 
            new_state = State.HAPPY
        elif self.scared_level > 5: # Check if scared
            new_state = State.SCARED
        elif now - self.last_pet_time > 80: # Handles attention decay (lonely)
            self.attention_level = max(0, self.attention_level - 10)
        if self.attention_level < 30 and self.state not in [State.SICK, State.DEAD]:
            new_state = State.LONELY
        if new_state not in [State.DEAD, State.SICK, State.SCARED, State.LONELY, State.HUNGRY]:
            new_state = State.HAPPY
        if new_state != self.state:
            print(f"[STATE CHANGE] {self.state.name} → {new_state.name}")
        self.state = new_state
        save_pet(self)

    def play(self): # Mini-game stuff
        if self.state == State.SAD:
            print("Playing cheered up the pet!")
            self.state = State.HAPPY

    def set_emotion(self, emotion):
        try:
            self.state = State[emotion.upper()]
            print(f"Pet emotion manually set to: {self.state}")
        except KeyError:
            print(f"Invalid emotion: {emotion}")

    def get_background_image(self): # Picks correct background image depending on theme + time
        theme = self.bg_theme.lower()
        valid_themes = ["city", "beach", "mountain"]
        if theme not in valid_themes:
            theme = "city"  # fallback
        now = datetime.now()
        is_night = now.hour < 7 or now.hour > 18
        time_of_day = "night" if is_night else "day"
        return f"/static/{theme}.{time_of_day}.png"


# ----- GLOBAL INSTANCE AND LOCK -----
_current_pet = load_pet()
pet_lock = threading.Lock()
_last_interaction_time = time.time()

# Helpers
def get_pet():
    return _current_pet

def get_pet_emotion():
    return _current_pet.state.name.lower()

def revive_pet():
    global _current_pet
    _current_pet = Pet()
    save_pet(_current_pet)

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker:", rc)
    client.subscribe("sandbox/fromMiddleHouse")

def on_message(client, userdata, msg): # Handle incoming messages
    global _last_interaction_time
    global game_feedback_msg
    payload_raw = msg.payload.decode()
    try:
        payload = json.loads(payload_raw)
    except Exception as e:
        print("Invalid JSON:", e)
        return

    house = payload.get("house")
    room = payload.get("room")
    component = payload.get("component")
    msg_value = payload.get("msg")
    value = payload.get("value")

    interaction_happened = False

    # --- HANDLE HIDE AND SEEK GUESS ---
    guess = None
    if _current_pet.hidden_room:
        if room == "bedroom" and component == "led" and msg_value.lower() == "led on":
            guess = "bedroom"
        elif room == "bathroom" and component in ["fan", "led"] and msg_value.lower() in ["on", "led on"]:
            guess = "bathroom"
        elif room == "living" and component == "pir" and msg_value.lower() == "pir on":
            guess = "living"
        elif room == "front" and component == "pir" and msg_value.lower() == "pir on":
            guess = "front"

    if guess:
        print(f"🏠 Hide and seek guess: {guess}")
        print(f"Hidden room: {_current_pet.hidden_room}")
        if guess == _current_pet.hidden_room:
            print("🎉 Pet found!")
            _current_pet.hidden_room = None
            game_feedback_msg = "correct"
        else:
            print("❌ Wrong room.")
            game_feedback_msg = "wrong"

        return  #Don't update state or scare pet after a hide n seek guess

    # --- NORMAL PET INTERACTIONS ---
    if house == "middle" and room == "bedroom" and component == "button" and msg_value == "pressed":
        _current_pet.feed()
        interaction_happened = True

    elif house == "middle" and room == "bedroom" and component == "led" and msg_value.lower() == "led on":
        if _current_pet.state == State.HUNGRY:
            _current_pet.feed()
            print("Pet fed via LED turning on")
            interaction_happened = True

    elif house == "middle" and room == "bathroom" and component == "button" and msg_value == "pressed":
        _current_pet.heal()
        interaction_happened = True

    elif house == "middle" and room in ["living", "front"] and component in ["pir", "led"] and msg_value.lower() in ["pir on", "led on"]:
        _current_pet.interact()
        interaction_happened = True
        print("Pet interacted with via motion sensor or LED")

    elif house == "middle" and room == "sensing" and component == "temp":
        try:
            _current_pet.temperature = float(value)
            _current_pet.check_temperature()
        except ValueError:
            print("Invalid temperature:", value)

    elif house == "middle" and room == "sensing" and component == "noise":
        if isinstance(value, (int, float)) and value > 50:
            _current_pet.hear_noise()

    elif house == "middle" and room == "sensing" and component == "gasConcentration":
        if isinstance(value, (int, float)) and value > 100:
            _current_pet.scared_level += 5
            _current_pet.sickness_level += 5

    elif house == "middle" and room == "bathroom" and component in ["fan", "led"] and msg_value.lower() in ["on", "led on"]:
        #Only scare if not hiding for hide n seek
        if not _current_pet.hidden_room:
            _current_pet.state = State.SCARED
            _current_pet.last_hint = "The fan is too loud and lights are too bright!!"
            print("Pet is scared due to fan or bright lights!") # Scared by fan/lights  

    elif house == "middle" and room == "bathroom" and component in ["fan", "led"] and msg_value.lower() in ["off", "led off"]:
        if _current_pet.state == State.SCARED:
            _current_pet.state = State.HAPPY
            _current_pet.last_hint = ""
            print("Fan and lights turned off — pet is calm again.")  #Calming down

    elif house == "middle" and room == "system" and component == "revive":
        revive_pet()
        print("Pet revived manually.")  # Manual revive

    # Update interaction timer
    if interaction_happened:
        _last_interaction_time = time.time()

    with pet_lock:
        _current_pet.update_state()

    # Debug output
    print("Pet state after update:", _current_pet.state)
    print("Hunger:", _current_pet.hunger_level)
    print("Attention:", _current_pet.attention_level)
    print("Scared:", _current_pet.scared_level)
    print("Temp:", _current_pet.temperature)
    print("Sickness:", _current_pet.sickness_level)

# Choose a room to hide in for the game
_current_pet.hidden_room = random.choice(HIDE_ROOMS)

#MQTT connect
client = mqtt.Client()
client.username_pw_set("student", "austral-clash-sawyer-blaze")
client.on_connect = on_connect
client.on_message = on_message
client.connect("mqtt.cci.arts.ac.uk", 1883, 60)

# Keeps pet updated every 5 secs
def periodic_update():
    while True:
        with pet_lock:
            _current_pet.update_state()
        time.sleep(5)

# Start everything
if __name__ == "__main__":
    threading.Thread(target=periodic_update, daemon=True).start()
    client.loop_forever()
else:
    client.loop_start()
    threading.Thread(target=periodic_update, daemon=True).start()
