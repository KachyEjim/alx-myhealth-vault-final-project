import pytest
from datetime import datetime, timedelta
from flask import Flask, jsonify, redirect, url_for
from api.app import app, db
from models.appointment import Appointment

@pytest.fixture
def client():

    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory test DB
    with app.app_context():
        db.create_all()  # Initialize the database for tests
        yield app.test_client()  # Provide the test client for tests
        db.session.remove()
        db.drop_all()  # Clean up after tests

def create_appointment(start_offset=0, end_offset=1, status="Notified"):
    """Helper function to create an appointment in the database."""
    start_time = (datetime.utcnow() + timedelta(hours=start_offset)).time()
    end_time = (datetime.utcnow() + timedelta(hours=end_offset)).time()
    appointment = Appointment(start_time=start_time, end_time=end_time, status=status)
    db.session.add(appointment)
    db.session.commit()
    return appointment.id

def test_appointment_not_found(client):
    """Test when appointment ID does not exist."""
    response = client.get("/join_appointment/999")  # Assuming 999 doesn't exist
    json_data = response.get_json()
    assert response.status_code == 404
    assert json_data['error'] == "APPOINTMENT_NOT_FOUND"

def test_appointment_valid_redirect(client):
    """Test when appointment is found and in 'Notified' status within valid time."""
    appointment_id = create_appointment(start_offset=-1, end_offset=1, status="Notified")
    response = client.get(f"/join_appointment/{appointment_id}")
    assert response.status_code == 302  # Redirect status
    assert response.headers['Location'] == "https://incomparable-parfait-456242.netlify.app/auth/login/?redirect_to=/appointments/reschedule"

def test_appointment_invalid_status(client):
    """Test when appointment is found but in a different status."""
    appointment_id = create_appointment(start_offset=-1, end_offset=1, status="Completed")  # Invalid status
    response = client.get(f"/join_appointment/{appointment_id}")
    json_data = response.get_json()
    assert response.status_code == 400
    assert json_data['error'] == "INVALID_APPOINTMENT_STATUS"

def test_appointment_invalid_time(client):
    """Test when appointment is found but not within the valid time range."""
    appointment_id = create_appointment(start_offset=-3, end_offset=-2, status="Notified")  # Out of time range
    response = client.get(f"/join_appointment/{appointment_id}")
    json_data = response.get_json()
    assert response.status_code == 400
    assert json_data['error'] == "INVALID_APPOINTMENT_STATUS"
