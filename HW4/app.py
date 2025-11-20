import os
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)

##mongo_uri = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017")
##client = MongoClient(mongo_uri)
client = MongoClient("mongodb+srv://eric:eric123456789@cluster0.11huqhs.mongodb.net/")
db = client["demoDB"]
collection = db["students"]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/insertMany", methods=["POST"])
def insert_many():
    docs = request.json
    result = collection.insert_many(docs)
    return jsonify({"insertedCount": len(result.inserted_ids)})

@app.route("/list", methods=["GET"])
def list_users():
    docs = list(collection.find({}))
    for d in docs:
        d["_id"] = str(d["_id"])
    return jsonify(docs)

@app.route("/deleteMany", methods=["POST"])
def delete_many():
    ids = request.json.get("ids", [])
    obj_ids = [ObjectId(i) for i in ids]
    result = collection.delete_many({"_id": {"$in": obj_ids}})
    return jsonify({"deletedCount": result.deleted_count})

if __name__ == "__main__":
    app.run(debug=True)
