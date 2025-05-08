from enum import Enum
import paho.mqtt.client as mqtt
import json
import time
import threading

# ----- PET STATE MACHINE -----

class State(Enum):
    HAPPY = "Happy"
    HUNGRY = "Hungry"
    LONELY = "Lonely"
    SAD = "Sad"
    SCARED = "Scared"
    SICK = "Sick"
    DEAD = "Dead"

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
        self.state_duration = 0
        self.sick_duration = 0
        self.last_hunger_update = time.time()

    def rename(self, new_name):
        self.name = new_name

    def feed(self):
        self.hunger_level = max(0, self.hunger_level - 10)
        self.last_hunger_update = time.time()
        self.hungry_duration = 0

    def interact(self):
        self.attention_level = min(100, self.attention_level + 10)
        if self.state == State.SCARED:
            self.scared_level = 0

    def check_temperature(self):
        if self.temperature < 15 or self.temperature > 30:
            self.sickness_level += 30

    def hear_noise(self):
        self.scared_level += 5

    def heal(self):
        if self.state == State.SICK:
            self.sickness_level = 0
            self.sick_duration = 0
            self.state = State.HAPPY

    def update_state(self):
        if self.state == State.DEAD:
            return

        if self.state == State.SICK:
            self.sick_duration += 1
            if self.sick_duration > 5:
                self.state = State.DEAD
            return

        # Hunger increases over time
        if time.time() - self.last_hunger_update > 10:
            self.hunger_level += 10
            self.hunger_level = min(self.hunger_level, 100)
            self.last_hunger_update = time.time()

        # Determine state
        if self.sickness_level > 50:
            new_state = State.SICK
        elif self.hunger_level > 70:
            new_state = State.HUNGRY
        elif self.attention_level < 30:
            new_state = State.LONELY
        elif self.scared_level > 5:
            new_state = State.SCARED
        else:
            new_state = State.HAPPY

        # Hungry duration tracking
        if new_state == State.HUNGRY:
            self.hungry_duration += 1
        else:
            self.hungry_duration = 0

        if self.hungry_duration >= 36:
            new_state = State.SICK
            self.hungry_duration = 0
            self.sick_duration = 0

        if new_state == self.state:
            self.state_duration += 1
        else:
            self.state_duration = 0

        self.state = new_state

        if self.state in [State.HUNGRY, State.LONELY, State.SAD, State.SCARED] and self.state_duration > 5:
            self.state = State.SICK
            self.state_duration = 0
            self.sick_duration = 0

# ----- GLOBAL PET INSTANCE -----
_current_pet = Pet()
_last_interaction_time = time.time()

def get_pet():
    return _current_pet

def get_pet_emotion():
    return _current_pet.state.name.lower()

def revive_pet():
    global _current_pet
    _current_pet = Pet()

# ----- MQTT CALLBACKS -----
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker:", rc)
    client.subscribe("sandbox/fromMiddleHouse") 

def on_message(client, userdata, msg):
    global _last_interaction_time

    payload_raw = msg.payload.decode()

    try:
        payload = json.loads(payload_raw)
    except Exception as e:
        print("Invalid JSON:", e)
        return

    print("\n--- MQTT Message Received ---")
    print("Payload:", payload)

    house = payload.get("house")
    room = payload.get("room")
    component = payload.get("component")
    msg_value = payload.get("msg")
    value = payload.get("value")

    interaction_happened = False

    # Feed via button
    if house == "middle" and room == "bedroom" and component == "button" and msg_value == "pressed":
        _current_pet.feed()
        interaction_happened = True

    # Feed via LED turning on — but only if hungry
    elif house == "middle" and room == "bedroom" and component == "led" and msg_value == "LED on":
        if _current_pet.state == State.HUNGRY:
            _current_pet.feed()
            print("Pet fed via LED turning on")
            interaction_happened = True
#
    # Heal via bathroom button
    elif house == "middle" and room == "bathroom" and component == "button" and msg_value == "pressed":
        _current_pet.heal()
        interaction_happened = True

    # Petting via PIR motion sensor
    elif house == "middle" and room in ["living", "front"] and component == "pir" and msg_value == "PIR on":
        _current_pet.interact()
        interaction_happened = True

    # Update temperature
    elif house == "middle" and room == "sensing" and component == "temp":
        try:
            _current_pet.temperature = float(value)
            _current_pet.check_temperature()
        except ValueError:
            print("Invalid temperature:", value)

    # Scare pet with noise
    elif house == "middle" and room == "sensing" and component == "noise":
        if isinstance(value, (int, float)) and value > 50:
            _current_pet.hear_noise()

    # Gas sensor input
    elif house == "middle" and room == "sensing" and component == "gasConcentration":
        if isinstance(value, (int, float)) and value > 100:
            _current_pet.scared_level += 5
            _current_pet.sickness_level += 5

    # Revive manually
    elif house == "middle" and room == "system" and component == "revive":
        revive_pet()
        print("Pet revived manually.")

    # Passive loneliness decay
    if time.time() - _last_interaction_time > 180:
        _current_pet.attention_level = max(0, _current_pet.attention_level - 50)

    if interaction_happened:
        _last_interaction_time = time.time()

    _current_pet.update_state()

    print("Pet state after update:", _current_pet.state)
    print("Hunger:", _current_pet.hunger_level)
    print("Attention:", _current_pet.attention_level)
    print("Scared:", _current_pet.scared_level)
    print("Temp:", _current_pet.temperature)
    print("Sickness:", _current_pet.sickness_level)

# ----- MQTT CLIENT SETUP -----
client = mqtt.Client()
client.username_pw_set("student", "austral-clash-sawyer-blaze") 
client.on_connect = on_connect
client.on_message = on_message
client.connect("mqtt.cci.arts.ac.uk", 1883, 60)

def periodic_update():
    while True:
        _current_pet.update_state()
        time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=periodic_update, daemon=True).start()
    client.loop_forever()
else:
    client.loop_start()
    threading.Thread(target=periodic_update, daemon=True).start()