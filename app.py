from flask import Flask, render_template, jsonify, request
from pet import get_pet_emotion, get_pet, revive_pet
import random

# Set up Flask app with template + static folders
app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)

# Globals for hide-and-seek
game_feedback_msg = ""
is_game_active = False

# ----------- HIDE AND SEEK ROUTES -----------
@app.route("/start_hide_seek")
def start_hide_seek():
    # pick a random room + start the game
    global is_game_active, game_feedback_msg  
    pet = get_pet()
    pet.hidden_room = random.choice(["bedroom", "living", "bathroom", "front"])
    is_game_active = True
    game_feedback_msg = ""  # reset feedback
    return jsonify({"status": "started"})

@app.route("/guess_room", methods=["GET"])
def guess_room():
    # check if player's guess is correct
    global is_game_active, game_feedback_msg
    pet = get_pet()
    guess = request.args.get("room")
    # pet isn't hiding, so guessing shouldn't do anything
    if not hasattr(pet, "hidden_room") or pet.hidden_room is None:
        game_feedback_msg = ""
        return jsonify({"message": "The pet isn't hiding right now!"})
    if guess == pet.hidden_room: # Correct guess
        pet.hidden_room = None
        game_feedback_msg = "correct"
        is_game_active = False
        return jsonify({"message": f"🎉 You found {pet.name}! They're thrilled!"})
    else:
        # wrong guess, try again
        game_feedback_msg = "wrong"
        return jsonify({"message": "❌ Not here. Try another room!"})

@app.route("/game_feedback") # Send result to frontend once, then clear it
def game_feedback():
    global game_feedback_msg
    result = game_feedback_msg
    game_feedback_msg = ""  # clear after sending to UI
    return jsonify({"result": result})

# ----------- ACTION ROUTES (BUTTONS / KEYS) -----------
@app.route("/action/name", methods=["POST"])
def rename_pet():
    data = request.get_json()  # Updates pet's name from user input
    new_name = data.get("name", "").strip()
    pet = get_pet()
    if new_name:
        pet.rename(new_name)
    return '', 204

@app.route("/action/revive")
def revive_pet_route():
    revive_pet() # Revives pet after it dies
    return '', 204

# Feeds pet + updates state
@app.route("/action/feed")
def feed_pet():
    pet = get_pet() 
    pet.feed()
    pet.update_state()
    return '', 204

 # Sets temp manually (for testing overheating)
@app.route("/action/temp")
def fan_on():
    pet = get_pet()
    pet.temperature = 25
    pet.update_state()
    return '', 204

 # Heals sick pet 
@app.route("/action/heal")
def heal_pet_action():
    pet = get_pet()
    pet.heal()
    pet.update_state()
    return jsonify({"status": "healed"})

 # Pet interaction — boosts attention
@app.route("/action/pet")
def pet_pet():
    pet = get_pet()
    pet.interact()
    pet.update_state()
    return '', 204

# ----------- DATA ROUTES -----------
 # Sends full pet state back to frontend
@app.route("/pet_state")
def pet_state():
    pet = get_pet()
    pet_emotion = pet.state.name.lower()
    pet_name = pet.name
    # Maps emotion to correct image
    emotion_to_image = {
        "happy": "pet_happy.png",
        "hungry": "pet_hungry.png",
        "lonely": "pet_lonely.png",
        "sad": "pet_sad.png",
        "scared": "pet_scared.png",
        "sick": "pet_sick.png",
        "dead": "pet_dead.png"
    }

    pet_image = emotion_to_image.get(pet_emotion, "pet_happy.png")

    return jsonify({
        "emotion": pet_emotion,
        "image": f"/static/{pet_image}",
        "name": pet_name,
        "hint": getattr(pet, "last_hint", ""),
        "background_image": pet.get_background_image(),
        "bg_theme": pet.bg_theme,
        "is_game_active": is_game_active 
    })

 # Update background theme from dropdown
@app.route('/set_theme', methods=['POST'])
def set_theme():
    theme = request.json.get("theme")
    if theme in ["city", "beach", "mountain"]:
        pet = get_pet()
        pet.set_theme(theme)
        return jsonify({"status": "ok"})
    return jsonify({"error": "invalid theme"}), 400

# ----------- PAGE RENDER -----------
# Render main HTML page
@app.route("/")
def home():
    return render_template("index.html")

# Run app in debug mode if started directly
if __name__ == "__main__":
    app.run(debug=True)
