from functools import wraps
from flask import session, redirect, url_for, jsonify
from typing import Callable, Any

def login_required(f: Callable) -> Callable:
    """
    Decorator to ensure user is logged in (Concept #2).
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if 'user_id' not in session:
            # You might want to redirect to a login page later
            # For now, return unauthorized or redirect to /login
            # Let's redirect to /login (which we'll create later)
            return redirect('/login') 
        return f(*args, **kwargs)
    return decorated_function

def role_required(role: str) -> Callable:
    """
    Decorator to restrict access based on user role (Concept #2).
    Must be used *after* @login_required.
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            user_role = session.get('role')
            if user_role != role:
                return jsonify({"success": False, "error": "Unauthorized"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def api_response(f: Callable) -> Callable:
    """
    Decorator to consistently wrap API responses (Concept #2).
    Expects function to return a dict or list for successful data,
    or a tuple (Dict, int) for errors/status codes.
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        try:
            result = f(*args, **kwargs)
            if isinstance(result, tuple):
                data, status_code = result
                # If the function already handled error formatting
                if "success" in data:
                    return jsonify(data), status_code
                return jsonify({"success": True if status_code < 400 else False, "data": data}), status_code
            
            return jsonify({"success": True, "data": result})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    return decorated_function
