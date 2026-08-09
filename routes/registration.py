from flask import Blueprint, render_template, request
import json
import uuid
from database.connection import DatabaseConnection
from utils.decorators import login_required, role_required, api_response
from utils.validators import validate_email, validate_phone, ValidationError

registration_bp = Blueprint('registration', __name__)

@registration_bp.route('/register/step/<int:step>')
@login_required
@role_required('admin')
def registration_step(step):
    template = f'registration_step{step}.html'
    return render_template(template)

@registration_bp.route('/api/register/save', methods=['POST'])
@login_required
@role_required('admin')
@api_response
def save_draft():
    data = request.json
    step = data.get('step', 1)
    ref_id = data.get('reference_id')
    
    if not ref_id:
        ref_id = f"DRAFT-{uuid.uuid4().hex[:8].upper()}"
        
    info_json = json.dumps(data.get('data', {}))
    
    with DatabaseConnection() as cursor:
        # Simplification: just upserting 
        cursor.execute("SELECT id FROM registration_drafts WHERE reference_id = ?", (ref_id,))
        existing = cursor.fetchone()
        
        if step == 1:
            col = "personal_info"
        elif step == 2:
            col = "academic_info"
        else:
            col = "guardian_info"
            
        if existing:
            cursor.execute(f"UPDATE registration_drafts SET {col} = ?, step = ?, updated_at = CURRENT_TIMESTAMP WHERE reference_id = ?", (info_json, step, ref_id))
        else:
            cursor.execute(f"INSERT INTO registration_drafts ({col}, reference_id, step) VALUES (?, ?, ?)", (info_json, ref_id, step))
            
    return {"reference_id": ref_id, "step": step, "message": "Draft saved automatically."}

@registration_bp.route('/api/register/submit', methods=['POST'])
@login_required
@role_required('admin')
@api_response
def submit_registration():
    data = request.json
    ref_id = data.get('reference_id')
    
    # In a real app we'd convert the draft into an actual student record here
    final_ref = f"ED-CONF-{uuid.uuid4().hex[:5].upper()}"
    
    with DatabaseConnection() as cursor:
        if ref_id:
            cursor.execute("UPDATE registration_drafts SET status = 'submitted' WHERE reference_id = ?", (ref_id,))
            
    return {"confirmation_id": final_ref, "message": "Registration Submitted"}

@registration_bp.route('/api/register/validate', methods=['POST'])
@api_response
def validate_field():
    data = request.json
    field = data.get('field')
    value = data.get('value')
    
    try:
        if field == 'email':
            validate_email(value)
        elif field == 'phone':
            validate_phone(value)
        return {"valid": True}
    except ValidationError as e:
        return {"valid": False, "error": str(e)}, 400
