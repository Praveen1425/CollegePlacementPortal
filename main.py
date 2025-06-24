# Import the app and run it
from app import create_app
import routes  # noqa: F401

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
