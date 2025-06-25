from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/assign-shift', methods=['POST'])
def assign_shift():
    data = request.json
    record_id = data.get('recordId')
    shift_id = data.get('shiftId')
    # Dummy response for now
    return jsonify({'message': 'Received', 'recordId': record_id, 'shiftId': shift_id})

if __name__ == '__main__':
    app.run(debug=True)
