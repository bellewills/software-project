from flask import Flask, render_template, jsonify, request
from pet import get_pet_emotion, get_pet, revive_pet

app = Flask(
    __name__,
    template_folder='templates',     # Flask finds index.html
    static_folder='static'          #Static images work
)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/action/name", methods=["POST"])
def rename_pet():
    data = request.get_json()
    new_name = data.get("name", "").strip()
    pet = get_pet()
    if new_name:
        pet.rename(new_name)
    return '', 204


@app.route("/action/revive")
def revive_pet_route():
    revive_pet()
    return '', 204

@app.route("/action/feed")
def feed_pet():
    pet = get_pet()
    pet.feed()
    pet.update_state()
    return '', 204

@app.route("/action/temp")
def fan_on():
    pet = get_pet()
    pet.temperature = 25
    pet.update_state()
    return '', 204

@app.route("/action/heal")
def heal_pet_action():
    pet = get_pet()
    pet.heal()
    pet.update_state()
    return jsonify({"status": "healed"})

@app.route("/action/pet")
def pet_pet():
    pet = get_pet()
    pet.interact()
    pet.update_state()
    return '', 204


@app.route("/pet_state")
def pet_state():
    pet = get_pet()
    pet_emotion = pet.state.name.lower()
    pet_name = pet.name  #Get the current name

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
        "name": pet_name  #Return the pet name to frontend
    })


if __name__ == "__main__":
    app.run(debug=True)
