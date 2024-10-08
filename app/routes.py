from flask import request, jsonify
from app import app

"""
This module contains the API logic for handling deposit and withdrawal events,
validating the request payload, and triggering alerts based on certain conditions.
"""


# Dictionary to store user actions for tracking
user_actions = {}


# Function to validate the incoming request payload
def validate_payload(data):
    """
    Validates the payload data to ensure it contains the required fields
    and follows the expected format.

    Args:
        data (dict): The incoming request data (JSON).

    Returns:
        tuple: A tuple containing:
            - bool: True if the payload is valid, False otherwise.
            - str: An error message if validation fails, otherwise None.
    """
    required_fields = ['type', 'amount', 'user_id', 'time']

    # Check if all required fields are present
    for field in required_fields:
        if field not in data:
            return False, f"Missing field: {field}"

    # Check if `type` is valid
    if data['type'] not in ['deposit', 'withdraw']:
        return False, "Invalid action type. Must be 'deposit' or 'withdraw'."

    # Check if `amount` can be converted to a float
    try:
        amount = float(data['amount'])
        if amount < 0:
            return False, "Amount cannot be negative."
    except ValueError:
        return False, "Invalid amount. Must be a valid number."

    # Check if `user_id` is an integer
    if not isinstance(data['user_id'], int):
        return False, "Invalid user_id. Must be an integer."

    # Check if `time` is an integer
    if not isinstance(data['time'], int):
        return False, "Invalid time. Must be an integer."

    # Ensure timestamps are sequential
    if data['user_id'] in user_actions:
        last_action = user_actions[data['user_id']][-1]
        if data['time'] <= last_action['time']:
            return False, "Time must be sequential and increasing."

    # All checks passed
    return True, None


@app.route('/event', methods=['POST'])
def event():
    """
    Handles the /event POST endpoint, which accepts deposit or withdrawal actions.
    Based on the actions provided, it may trigger alerts if certain conditions are met.

    Returns:
        Response: A JSON response containing:
            - alert (bool): Indicates whether an alert was triggered.
            - alert_codes (list): List of triggered alert codes.
            - user_id (int): The user ID associated with the action.
    """
    data = request.json
    print(f"Received request data: {data}")  # Log the incoming request data

    # Validate the request payload
    is_valid, error_message = validate_payload(data)

    # If payload validation fails, return a 400 Bad Request
    if not is_valid:
        print(f"Validation failed: {error_message}")  # Log validation failure reason
        return jsonify({"error": error_message}), 400

    user_id = data['user_id']

    # Initialize user history if necessary
    if user_id not in user_actions:
        user_actions[user_id] = []

    user_actions[user_id].append(data)
    alert_codes = []

    # Code 1100: Withdrawal Over 100
    if data['type'] == 'withdraw' and float(data['amount']) > 100:
        alert_codes.append(1100)

    # Code 30: 3 Consecutive Withdrawals
    if len(user_actions[user_id]) >= 3:
        recent_actions = user_actions[user_id][-3:]
        if all(action['type'] == 'withdraw' for action in recent_actions):
            alert_codes.append(30)

    # Code 300: 3 Increasing Deposits
    deposits = [action for action in user_actions[user_id] if action['type'] == 'deposit']
    if len(deposits) >= 3 and deposits[-1]['amount'] > deposits[-2]['amount'] > deposits[-3]['amount']:
        alert_codes.append(300)

    # Code 123: Total Deposits Exceed 200 in 30 Seconds
    current_time = data['time']
    recent_deposits = [
        action for action in user_actions[user_id]
        if action['type'] == 'deposit' and current_time - action['time'] <= 30
    ]
    total_deposits = sum(float(deposit['amount']) for deposit in recent_deposits)
    if total_deposits > 200:
        alert_codes.append(123)

    print(f"Returning alert codes: {alert_codes}")  # Log the generated alert codes

    # Return the response as JSON
    return jsonify({
        "alert": bool(alert_codes),
        "alert_codes": alert_codes,
        "user_id": user_id
    })