from threading import Thread
from flask import Flask

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return "ok", 200

def start_api():
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

def run_api():
    # Inicia a API em segundo plano
    api_thread = Thread(target=start_api)
    api_thread.daemon = True
    api_thread.start()
