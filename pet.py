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
        self.sick_duration = 0
        self.last_hunger_update = time.time()
        self.last_hint = ""
        self.last_pet_time = time.time()

    def rename(self, new_name):
        self.name = new_name

    def feed(self):
        self.hunger_level = max(0, self.hunger_level - 10)
        self.last_hunger_update = time.time()
        self.hungry_duration = 0

    def interact(self):
        self.attention_level = min(100, self.attention_level + 10)
        self.last_pet_time = time.time()
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
            print("Pet is dead. update_state() skipped.")
            return

        if time.time() - self.last_hunger_update > 10:
            self.hunger_level += 10
            self.hunger_level = min(self.hunger_level, 100)
            self.last_hunger_update = time.time()

        if self.state == State.SICK:
            if self.sickness_level > 50:
                self.sick_duration += 1
                print(f"Sick duration: {self.sick_duration}")
                if self.sick_duration > 5:
                    self.state = State.DEAD
                    print("Pet has died from prolonged sickness.")
                    return
            else:
                print("Sickness level dropped — exiting sick state.")
                self.state = State.HAPPY
                self.sick_duration = 0

        if self.sickness_level > 50 and self.state != State.SICK:
            self.state = State.SICK
            self.sick_duration = 0
            print("Pet is now sick.")
            return

        if self.scared_level > 5 or self.state == State.SCARED:
            self.state = State.SCARED
            return

        if time.time() - self.last_pet_time > 80:
            self.attention_level = max(0, self.attention_level - 10)

        if self.attention_level < 30:
            self.state = State.LONELY
            return

        if self.hunger_level > 70:
            self.state = State.HUNGRY
            self.hungry_duration += 1
        else:
            self.hungry_duration = 0

        if self.hungry_duration >= 36:
            self.state = State.SICK
            self.hungry_duration = 0
            self.sick_duration = 0
            print("Pet became sick due to starvation.")
            return

        self.state = State.HAPPY

    def play(self):
        if self.state == State.SAD:
            print("Playing cheered up the pet!")
            self.state = State.HAPPY

    def set_emotion(self, emotion):
        try:
            self.state = State[emotion.upper()]
            print(f"Pet emotion manually set to: {self.state}")
        except KeyError:
            print(f"Invalid emotion: {emotion}")

# ----- GLOBAL INSTANCE AND LOCK -----
_current_pet = Pet()
pet_lock = threading.Lock()
_last_interaction_time = time.time()

def get_pet():
    return _current_pet

def get_pet_emotion():
    return _current_pet.state.name.lower()

def revive_pet():
    global _current_pet
    _current_pet = Pet()

# ----- MQTT SETUP -----
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

    if house == "middle" and room == "bathroom" and component in ["fan", "led"] and msg_value.lower() in ["on", "led on"]:
        _current_pet.state = State.SCARED
        _current_pet.last_hint = "The fan is too loud and lights are too bright!!"
        print("Pet is scared due to fan or bright lights!")

    elif house == "middle" and room == "bathroom" and component in ["fan", "led"] and msg_value.lower() in ["off", "led off"]:
        if _current_pet.state == State.SCARED:
            _current_pet.state = State.HAPPY
            _current_pet.last_hint = ""
            print("Fan and lights turned off — pet is calm again.")

    elif house == "middle" and room == "system" and component == "revive":
        revive_pet()
        print("Pet revived manually.")

    if interaction_happened:
        _last_interaction_time = time.time()

    with pet_lock:
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
        with pet_lock:
            _current_pet.update_state()
        time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=periodic_update, daemon=True).start()
    client.loop_forever()
else:
    client.loop_start()
    threading.Thread(target=periodic_update, daemon=True).start()
