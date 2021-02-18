# USAGE
# gunicorn --bind 0.0.0.0:8001 --worker-class eventlet -w 1 wsgi:app

from fserver import app

if __name__ == "__main__":
    print("Start the wsgi server!")

    app.run(debug=False)
    #socketio.run(app, host="localhost", port=8001, debug=False)