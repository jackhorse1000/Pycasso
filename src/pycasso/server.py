from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


def main() -> None:
    app.run()


if __name__ == "__main__":
    main()
