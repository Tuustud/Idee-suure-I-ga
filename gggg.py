from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate():
    
    data = request.get_json()

    free_time = data.get('free_time')
    time_unit = data.get('time_unit')
    location = data.get('location')
    tools = data.get('tools', [])  
    
    activity_suggestion = 

    return jsonify({
        "status": "success",
        "message": 
    })