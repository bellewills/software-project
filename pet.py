from enum import Enum
import paho.mqtt.client as mqtt

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
        self.attention_level = 100
        self.temperature = 22.0
        self.scared_level = 0
        self.sickness_level = 0
        self.state_duration = 0
        self.sick_duration = 0

    def rename(self, new_name): # Method to change the name
        self.name = new_name

    def feed(self):
        self.hunger_level = max(0, self.hunger_level - 10)

    def interact(self):
        self.attention_level = min(100, self.attention_level + 10)

    def check_temperature(self):
        if self.temperature < 15 or self.temperature > 30:
            self.sickness_level += 10

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
    client.subscribe("pet/button")
    client.subscribe("pet/temperature")
    client.subscribe("pet/noise")
    client.subscribe("pet/attention")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    print(f"\n--- MQTT Message Received ---")
    print("Topic:", topic)
    print("Payload:", payload)

    if topic == "pet/button":
        if payload == "feed":
            _current_pet.feed()
        elif payload == "interact":
            _current_pet.interact()
        elif payload == "heal":
            _current_pet.heal()

    elif topic == "pet/temperature":
        try:
            _current_pet.temperature = float(payload)
            _current_pet.check_temperature()
        except ValueError:
            print("Invalid temperature:", payload)

    elif topic == "pet/noise":
        if payload == "loud":
            _current_pet.hear_noise()

    elif topic == "pet/attention":
        _current_pet.attention_level = max(0, min(100, int(payload)))

    _current_pet.update_state()
    print("Pet state after update:", _current_pet.state)
    print("Hunger:", _current_pet.hunger_level, "Attention:", _current_pet.attention_level,
          "Scared:", _current_pet.scared_level, "Temp:", _current_pet.temperature, "Sickness:", _current_pet.sickness_level)

# ----- MQTT CLIENT SETUP -----
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)

if __name__ == "__main__":
    client.loop_forever()
else:
    client.loop_start()
