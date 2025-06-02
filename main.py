
from flask import Flask, request, make_response, jsonify, render_template
from pony import orm
from datetime import datetime

DB = orm.Database()
app = Flask(__name__)


class Location(DB.Entity):
    location_id = orm.PrimaryKey(int, auto=True)
    sea = orm.Required(str)
    temperature = orm.Required(float)
    salinity = orm.Required(float)
    waves = orm.Required(str)
    quality = orm.Required(str)

DB.bind(provider="sqlite", filename="database.sqlite", create_db=True)
DB.generate_mapping(create_tables=True)


def add_location(json_request):
    try:
        sea = json_request["sea"]
        temperature = float(json_request["temperature"])
        salinity = float(json_request["salinity"])
        waves = json_request["waves"]
        quality = json_request["quality"]

        with orm.db_session:
            Location(sea=sea, temperature=temperature, salinity=salinity, waves=waves, quality=quality)
            return {"response": "Success"}
    except Exception as e:
        return {"response": "Fail", "error": str(e)}

def get_locations():
    try:
        with orm.db_session:
            # Sortiranje po nazivu mora u upitu
            db_query = orm.select(x for x in Location).order_by(Location.sea)[:]
            results_list = [loc.to_dict() for loc in db_query]
            return {"response": "Success", "data": results_list}
    except Exception as e:
        return {"response": "Fail", "error": str(e)}

def get_location_by_id(location_id):
    try:
        with orm.db_session:
            result = Location[location_id].to_dict()
            return {"response": "Success", "data": result}
    except Exception as e:
        return {"response": "Fail", "error": str(e)}

def update_location(location_id, json_request):
    try:
        with orm.db_session:
            to_update = Location[location_id]
            if 'sea' in json_request:
                to_update.sea = json_request['sea']
            if 'temperature' in json_request:
                to_update.temperature = float(json_request['temperature'])
            if 'salinity' in json_request:
                to_update.salinity = float(json_request['salinity'])
            if 'waves' in json_request:
                to_update.waves = json_request['waves']
            if 'quality' in json_request:
                to_update.quality = json_request['quality']
            return {"response": "Success"}
    except Exception as e:
        return {"response": "Fail", "error": str(e)}

def delete_location(location_id):
    try:
        with orm.db_session:
            to_delete = Location[location_id]
            to_delete.delete()
            return {"response": "Success"}
    except Exception as e:
        return {"response": "Fail", "error": str(e)}


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dodaj/lokaciju", methods=["GET", "POST"])
def dodaj_location():
    if request.method == "POST":
        json_request = {key: value for key, value in request.form.items()}
        response = add_location(json_request)
        if response["response"] == "Success":
            return render_template("dodaj.html")
        return jsonify(response), 400
    return render_template("dodaj.html")

@app.route("/lokacija/<int:location_id>", methods=["PUT"])
def zamijeni_location(location_id):
    try:
        json_request = request.json
    except Exception as e:
        return jsonify({"response": "Fail", "error": str(e)}), 400

    required_fields = {"sea", "temperature", "salinity", "waves", "quality"}
    if not required_fields.issubset(json_request):
        return jsonify({"response": "Fail", "error": "Nedostaju neka polja za potpunu zamjenu"}), 400

    try:
        with orm.db_session:
            loc = Location[location_id]
            loc.sea = json_request["sea"]
            loc.temperature = float(json_request["temperature"])
            loc.salinity = float(json_request["salinity"])
            loc.waves = json_request["waves"]
            loc.quality = json_request["quality"]
        return jsonify({"response": "Success"}), 200
    except Exception as e:
        return jsonify({"response": "Fail", "error": str(e)}), 400

@app.route("/vrati/lokacije", methods=["GET"])
def vrati_locations():
    if 'id' in request.args:
        try:
            location_id = int(request.args.get("id"))
            response = get_location_by_id(location_id)
            if response["response"] == "Success":
                return render_template("vrati.html", data=[response["data"]])
            return jsonify(response), 400
        except ValueError:
            return jsonify({"response": "Fail", "error": "Neispravan ID"}), 400

    response = get_locations()
    if response["response"] == "Success":
        return render_template("vrati.html", data=response["data"])
    return jsonify(response), 400

@app.route("/lokacija/<int:location_id>", methods=["DELETE"])
def obrisi_location(location_id):
    response = delete_location(location_id)
    return jsonify(response), 200 if response["response"] == "Success" else 400

@app.route("/lokacija/<int:location_id>", methods=["PATCH"])
def izmjeni_location(location_id):
    try:
        json_request = request.json
    except Exception as e:
        return jsonify({"response": "Fail", "error": str(e)}), 400
    response = update_location(location_id, json_request)
    return jsonify(response), 200 if response["response"] == "Success" else 400

@app.route("/vizualizacija")
def vizualizacija():
    try:
        with orm.db_session:
            locations = orm.select(l for l in Location)[:]
            counts = {}
            for loc in locations:
                quality = loc.quality or "Nepoznato"
                counts[quality] = counts.get(quality, 0) + 1

            x_axis = list(counts.keys())
            y_axis = list(counts.values())

        return render_template("vizualizacija.html", x_axis=x_axis, y_axis=y_axis)
    except Exception as e:
        return jsonify({"response": "Fail", "error": str(e)}), 500

@app.route("/salinitet")
def salinitet():
    try:
        with orm.db_session:
            data = orm.select(l for l in Location)[:]
            salinity_data = {}

            for loc in data:
                if loc.sea not in salinity_data:
                    salinity_data[loc.sea] = []
                salinity_data[loc.sea].append(loc.salinity)

            x_axis = list(salinity_data.keys())
            y_axis = [round(sum(vals) / len(vals), 2) for vals in salinity_data.values()]

        return render_template("salinitet.html", x_axis=x_axis, y_axis=y_axis)
    except Exception as e:
        return jsonify({"response": "Fail", "error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=8080)
