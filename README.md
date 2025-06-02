# Virtual Pet IoT Project  

## Overview 
This is a browser-based Virtual Pet that lives inside a physical IoT house. Users must care for the pet by feeding, petting, and healing it using live sensor input from the house. The pet responds emotionally in real time and includes a mini hide-and-seek game for added interactivity.

## How It Works
- The pet lives in a virtual UI but responds to actions taken in a real, physical IoT house.
- The house contains sensors (motion, LEDs, fan, button) that send messages using MQTT.
- A Python backend (Flask) handles these messages and updates the pet's emotional state using a **state machine**.
- The browser-based UI shows how the pet feels with animations, music, and sound effects.

## How to Run

1. Run the Flask App
In terminal, in the correct cd / file path run: python app.py
Then open your browser and go to http://localhost:5000

3. Open MQTT Explorer
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

## Features

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

## Notes:

Browser Audio Restrictions: Most browsers (especially Chrome and Safari) block autoplay of sound or music until the user interacts with the page. You may need to interact with the UI (e.g. naming or renaming your pet, adjusting the volume sliders, or selecting a home theme) before any music or sound effects will start playing.

First-Time MQTT Setup: Make sure your device is connected to the same Wi-Fi network as the IoT house. If MQTT Explorer doesn’t show data, double-check your connection and topic subscription.

Mock Data for Testing: You can manually send MQTT payloads to test pet state changes. For example:

To simulate overheating (scared state), send a high temperature payload like { "temp": 35 }.

To heal or interact with the pet, publish other mock values matching your expected sensor inputs (e.g. motion: true, fan: on).

Use topic: sandbox/fromMiddleHouse and ensure JSON format matches what the Flask backend expects.

Offline Testing Shortcuts: If you don’t have access to the physical IoT house, use the UI buttons or keyboard shortcuts:

Press H = Heal

Press F = Feed

Press T = Simulate high temp (scared)

Game Mode Behaviour: While in Hide and Seek mode, the pet won’t become sad, scared, or hungry. Sensor inputs are used purely as guesses and won’t affect its emotional state.

## Credits

##### Code: Belle Williams (lead dev), Keya Datta (UI / Design and documentation)

Background art (AI-generated): via ChatGPT

Pet design / Character: Belle Williams & Keya Datta

##### Sound effects:

Freesound.org

Pixabay

Project template from UAL Software Engineering Template
