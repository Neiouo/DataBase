from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient

app = Flask(__name__)

# Connect to local MongoDB
client = MongoClient("mongodb://atlas-sql-6919334b0c292835c9c1486a-gjnqqq.a.query.mongodb.net/demoDB?ssl=true&authSource=admin")
db = client["demoDB"]
collection = db["students"]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/insertMany", methods=["POST"])
def insert_many():
    try:
        docs = request.json  # expects array of objects
        result = collection.insert_many(docs)
        return jsonify({
            "insertedCount": len(result.inserted_ids),
            "insertedIds": [str(i) for i in result.inserted_ids]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/list", methods=["GET"])
def list_users():
    try:
        docs = list(collection.find({}))
        # Convert ObjectId to string
        for d in docs:
            d["_id"] = str(d["_id"])
        return jsonify(docs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(debug=True)

