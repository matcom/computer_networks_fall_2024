from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": 200, "body": "Welcome to the server!", "headers": dict(request.headers)})

@app.route("/", methods=["POST"])
def post_example():
    return jsonify({"status": 200, "body": "POST request successful", "headers": dict(request.headers)})

@app.route("/", methods=["HEAD"])
def head_example():
    return "", 200

@app.route("/secure", methods=["GET", "POST"])
def secure():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return jsonify({"status": 401, "body": "Authorization header missing"}), 401

    if auth_header != "Bearer 12345":
        return jsonify({"status": 401, "body": "Invalid or missing authorization token"}), 401

    if request.method == "GET":
        return jsonify({"status": 200, "body": "You accessed a protected resource"})

    if request.method == "POST":
        try:
            json_data = request.get_json()
            if json_data is None:
                raise ValueError
        except:
            return jsonify({"status": 400, "body": "Malformed JSON body"}), 400
        return jsonify({"status": 200, "body": "POST received in secure area"})

@app.route("/resource", methods=["PUT"])
def put_resource():
    return jsonify({"status": 200, "body": "PUT request successful! Resource '/resource' would be updated if this were implemented."})

@app.route("/resource", methods=["DELETE"])
def delete_resource():
    return jsonify({"status": 200, "body": "DELETE request successful! Resource '/resource' would be deleted if this were implemented."})

@app.route("/", methods=["OPTIONS"])
def options_example():
    return "", 204

@app.route("/", methods=["TRACE"])
def trace_example():
    return jsonify({"status": 200, "body": "TRACE method successful"})

@app.route("/target", methods=["CONNECT"])
def connect_example():
    return jsonify({"status": 200, "body": "CONNECT method successful"})

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"status": 405, "body": "Method Not Allowed"}), 405

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

