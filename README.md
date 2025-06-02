#Virtual Pet IoT Project
This is a browser-based Virtual Pet that lives inside a physical IoT house. Users must care for the pet by feeding, petting, and healing it using live sensor input from the house. The pet responds emotionally in real time and includes a mini hide-and-seek game for added interactivity.

How It Works
The project uses a Raspberry Pi in a custom-built IoT house.

Data from motion sensors, LEDs, a button, and a fan is published via MQTT and handled by a Flask backend.

The backend maintains the pet’s emotional state using a state machine (happy, sad, scared, hungry, sick, lonely, dead).

The frontend reflects these states through dynamic visuals, sound effects, and background music.

How to Run
1. Run the Flask App
python app.py
Then open your browser and go to http://localhost:5000

2. Open MQTT Explorer
Connect to: mqtt.cci.arts.ac.uk
- Make sure you are on the same network the IOT house is on for first time connecting. - 

Subscribe to:
sandbox/fromMiddleHouse

3. Interacting with the Pet
Emotion	How to Trigger	How to Fix
Hungry	Wait 60s	Toggle bedroom LED on/off
Sick	Send "sick" payload via MQTT	Toggle bedroom LED to "heal"
Lonely	Wait 180s without interaction	Wave hand over living room sensor
Scared	Turn on fan or lights in bathroom	Turn them off again
Sad	Ignore when lonely/scared	Pet it or give attention
Dead	Wait too long without help	Press "Revive"

Hints appear in the UI when something is wrong.

Hide and Seek Game Mode
Click “Play a Game” when the pet is happy to enter Hide and Seek mode.

You can guess where the pet is hiding by:

Living Room → Move near the motion sensor

Bathroom → Turn on fan/LED

Bedroom → Toggle bedroom LED

Front Porch → Trigger outdoor motion

Guesses use IoT actions only — the pet won’t get scared or sad during the game.

Features
Custom pixel-art pet images with animated states

Emotion-based music and SFX (autoplay fixed)

Volume sliders + mute buttons

State persistence using JSON

Fully commented frontend and backend code

Optional keyboard testing (H = Heal, F = Feed, T = Temp)

Technologies Used
Python (Flask)

JavaScript

HTML/CSS

MQTT via paho-mqtt

IOT House 

Credits
Code: Belle Williams (lead dev), Keya Datta (UI / Design and documentation)

Background art (AI-generated): via ChatGPT

Pet design / Character: Belle Williams & Keya Datta

Sound effects:

Freesound.org

Pixabay

Project template from UAL Software Engineering Template
