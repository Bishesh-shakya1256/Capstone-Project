"""
routes.py - Flask API Routes
"""

from flask import Blueprint, request, jsonify, session
from app import db_utils
from app.models import db, User, Plant, PlantCategory
from app.decorators import login_required, admin_required
import bcrypt

main = Blueprint("main", __name__)


VALID_LIGHT = {"Low", "Medium", "High"}
VALID_MAINTENANCE = {"Low", "Medium", "High"}
VALID_SIZE = {"Small", "Medium", "Large"}
VALID_TOXICITY = {"Non-toxic", "Mildly toxic", "Toxic"}
VALID_GROWTH = {"Slow", "Moderate", "Fast"}
VALID_HUMIDITY = {"Low", "Medium", "High"}
VALID_TEMP = {"Cool", "Moderate", "Warm"}
VALID_EXPERIENCE = {"Beginner", "Intermediate", "Expert"}


# Helper: get user/guest from session
def get_session_identity():
    return session.get("user_id"), session.get("guest_id")


# AUTH ROUTES

@main.route("/api/register", methods=["POST"])
def register():
    """Register a new user."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    required = ["name", "email", "password", "experience_level"]
    for field in required:
        if field not in data or not str(data[field]).strip():
            return jsonify({"success": False, "error": f"Missing field: {field}"}), 400

    result = db_utils.register_user(
        name=data["name"],
        email=data["email"],
        password=data["password"],
        experience_level=data["experience_level"]
    )

    if result["success"]:
        session["user_id"] = result["user_id"]
        session.pop("guest_id", None)
        return jsonify(result), 201
    return jsonify(result), 409


@main.route("/api/login", methods=["POST"])
def login():
    """Login an existing user."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    if "email" not in data or "password" not in data:
        return jsonify({"success": False, "error": "email and password required"}), 400

    result = db_utils.login_user(data["email"], data["password"])

    if result["success"]:
        session["user_id"] = result["user"]["user_id"]
        session.pop("guest_id", None)
        return jsonify(result), 200
    return jsonify(result), 401


@main.route("/api/logout", methods=["POST"])
def logout():
    """Clear the session."""
    session.clear()
    return jsonify({"success": True, "message": "Logged out"}), 200


@main.route("/api/guest", methods=["POST"])
def guest_session():
    """Create a guest session."""
    result = db_utils.create_guest_session()
    if result["success"]:
        session["guest_id"] = result["guest_id"]
        session.pop("user_id", None)
        return jsonify(result), 201
    return jsonify(result), 500


# PREFERENCES & ENVIRONMENT ROUTES

@main.route("/api/preferences", methods=["GET"])
def get_preferences():
    """Load saved preferences for the logged-in user."""
    user_id, _ = get_session_identity()
    if not user_id:
        return jsonify({"success": True, "preference": None})
    result = db_utils.get_user_preference(user_id)
    user = User.query.get(user_id)
    if user and result.get("preference"):
        result["preference"]["experience_level"] = user.experience_level
    return jsonify(result)


@main.route("/api/preferences", methods=["POST"])
def save_preferences():
    """Save user preferences (registered users only)."""
    user_id, _ = get_session_identity()
    if not user_id:
        return jsonify({"success": False, "error": "Login required"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    required = ["preferred_light", "preferred_maintenance", "preferred_size"]
    for field in required:
        if field not in data:
            return jsonify({"success": False, "error": f"Missing field: {field}"}), 400

    result = db_utils.save_user_preference(
        user_id=user_id,
        preferred_light=data["preferred_light"],
        preferred_maintenance=data["preferred_maintenance"],
        preferred_size=data["preferred_size"],
        pet_friendly_required=data.get("pet_friendly_required", False)
    )

    status = 200 if result["success"] else 400
    return jsonify(result), status


@main.route("/api/preferences", methods=["DELETE"])
def delete_preferences():
    """Delete saved preferences for the logged-in user."""
    from app.models import UserPreference
    user_id, _ = get_session_identity()
    if not user_id:
        return jsonify({"success": False, "error": "Login required"}), 401
    deleted = UserPreference.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify({"success": True, "deleted": deleted})


@main.route("/api/environment", methods=["POST"])
def save_environment():
    """Save user environment data (registered users only)."""
    user_id, _ = get_session_identity()
    if not user_id:
        return jsonify({"success": False, "error": "Login required"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    required = ["light_level", "humidity", "temperature", "room_size"]
    for field in required:
        if field not in data:
            return jsonify({"success": False, "error": f"Missing field: {field}"}), 400

    result = db_utils.save_environment(
        user_id=user_id,
        light_level=data["light_level"],
        humidity=data["humidity"],
        temperature=data["temperature"],
        room_size=data["room_size"]
    )

    status = 200 if result["success"] else 400
    return jsonify(result), status


# INTERACTION, RATING, REVIEW ROUTES

@main.route("/api/interact", methods=["POST"])
def interact():
    """Log a plant interaction (user or guest)."""
    user_id, guest_id = get_session_identity()
    if not user_id and not guest_id:
        return jsonify({"success": False, "error": "Session required"}), 401

    data = request.get_json()
    if not data or "plant_id" not in data or "interaction_type" not in data:
        return jsonify({"success": False, "error": "plant_id and interaction_type required"}), 400

    try:
        plant_id = int(data["plant_id"])
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "plant_id must be a number"}), 400

    result = db_utils.log_interaction(
        plant_id=plant_id,
        interaction_type=str(data["interaction_type"])[:50],
        user_id=user_id,
        guest_id=guest_id
    )

    status = 201 if result["success"] else 400
    return jsonify(result), status


@main.route("/api/rate", methods=["POST"])
def rate_plant():
    """Rate a plant 1-5 (registered users only)."""
    user_id, _ = get_session_identity()
    if not user_id:
        return jsonify({"success": False, "error": "Login required to rate plants"}), 401

    data = request.get_json()
    if not data or "plant_id" not in data or "rating_value" not in data:
        return jsonify({"success": False, "error": "plant_id and rating_value required"}), 400

    try:
        plant_id = int(data["plant_id"])
        rating_value = int(data["rating_value"])
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "plant_id and rating_value must be numbers"}), 400

    if rating_value < 1 or rating_value > 5:
        return jsonify({"success": False, "error": "rating_value must be 1-5"}), 400

    result = db_utils.submit_rating(
        user_id=user_id,
        plant_id=plant_id,
        rating_value=rating_value
    )

    status = 200 if result["success"] else 400
    return jsonify(result), status


@main.route("/api/review", methods=["POST"])
def review_plant():
    """Submit a text review (registered users only)."""
    user_id, _ = get_session_identity()
    if not user_id:
        return jsonify({"success": False, "error": "Login required to write reviews"}), 401

    data = request.get_json()
    if not data or "plant_id" not in data or "review_text" not in data:
        return jsonify({"success": False, "error": "plant_id and review_text required"}), 400

    try:
        plant_id = int(data["plant_id"])
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "plant_id must be a number"}), 400

    review_text = str(data["review_text"]).strip()
    if not review_text:
        return jsonify({"success": False, "error": "review_text cannot be empty"}), 400
    if len(review_text) > 2000:
        return jsonify({"success": False, "error": "review_text must be under 2000 characters"}), 400

    result = db_utils.submit_review(
        user_id=user_id,
        plant_id=plant_id,
        review_text=review_text
    )

    status = 201 if result["success"] else 400
    return jsonify(result), status


# RECOMMENDATION ROUTES

@main.route("/api/recommend", methods=["POST"])
def recommend():
    """Generate and store recommendations."""
    user_id, guest_id = get_session_identity()

    if not user_id and not guest_id:
        return jsonify({"success": False, "error": "Session required"}), 401

    if user_id:
        result = db_utils.generate_cf_recommendation(user_id=user_id)
    else:
        result = db_utils.generate_guest_recommendation(guest_id=guest_id)

    status = 200 if result["success"] else 500
    return jsonify(result), status


@main.route("/api/recommendations", methods=["GET"])
def get_recommendations():
    """Retrieve stored recommendations for current session."""
    user_id, guest_id = get_session_identity()

    if not user_id and not guest_id:
        return jsonify({"success": False, "error": "Session required"}), 401

    result = db_utils.get_recommendations(user_id=user_id, guest_id=guest_id)
    return jsonify(result), 200


# PLANT ROUTES

@main.route("/api/plants", methods=["GET"])
def get_plants():
    """Get all plants."""
    result = db_utils.get_all_plants()
    return jsonify(result), 200


@main.route("/api/plants/<int:plant_id>", methods=["GET"])
def get_plant(plant_id):
    """Get a single plant by ID."""
    result = db_utils.get_plant_by_id(plant_id)
    status = 200 if result["success"] else 404
    return jsonify(result), status


# ==========================================
# PLANT CRUD ROUTES (admin only)
# ==========================================

@main.route("/api/plants", methods=["POST"])
@admin_required
def create_plant():
    """Create a new plant (admin)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    plant_name = (data.get("plant_name") or "").strip()
    if not plant_name:
        return jsonify({"error": "Plant name is required"}), 400
    if len(plant_name) > 200:
        return jsonify({"error": "Plant name must be under 200 characters"}), 400

    category_name = (data.get("category_name") or "General").strip()
    category_id = data.get("category_id")

    if category_id:
        try:
            category_id = int(category_id)
        except (ValueError, TypeError):
            return jsonify({"error": "category_id must be a number"}), 400
        cat = PlantCategory.query.get(category_id)
        if not cat:
            return jsonify({"error": f"Invalid category_id: {category_id}"}), 400
    else:
        cat = PlantCategory.query.filter_by(category_name=category_name).first()
        if not cat:
            cat = PlantCategory(category_name=category_name[:100])
            db.session.add(cat)
            db.session.flush()
        category_id = cat.category_id

    if Plant.query.filter_by(plant_name=plant_name).first():
        return jsonify({"error": f"Plant '{plant_name}' already exists"}), 409

    plant = Plant(
        plant_name=plant_name,
        category_id=category_id,
        light_requirement=data.get("light_requirement", "Medium"),
        watering_frequency=(data.get("watering_frequency") or "Weekly")[:50],
        maintenance_level=data.get("maintenance_level", "Medium"),
        humidity_requirement=data.get("humidity_requirement", "Medium"),
        temperature_range=data.get("temperature_range", "Moderate"),
        toxicity_level=data.get("toxicity_level", "Non-toxic"),
        growth_rate=data.get("growth_rate", "Moderate"),
        size_category=data.get("size_category", "Medium"),
        image_url=(data.get("image_url") or "")[:500] or None
    )
    db.session.add(plant)
    db.session.commit()
    result = plant.to_dict()
    result["category_name"] = category_name
    return jsonify(result), 201


@main.route("/api/plants/<int:plant_id>", methods=["PUT"])
@admin_required
def update_plant(plant_id):
    """Update a plant (admin)."""
    plant = Plant.query.get(plant_id)
    if not plant:
        return jsonify({"error": "Plant not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "plant_name" in data:
        name = str(data["plant_name"]).strip()
        if not name:
            return jsonify({"error": "Plant name cannot be empty"}), 400
        if len(name) > 200:
            return jsonify({"error": "Plant name must be under 200 characters"}), 400
        existing = Plant.query.filter_by(plant_name=name).first()
        if existing and existing.plant_id != plant_id:
            return jsonify({"error": "A plant with that name already exists"}), 409
        plant.plant_name = name
    if "light_requirement" in data:
        plant.light_requirement = str(data["light_requirement"])[:50]
    if "watering_frequency" in data:
        plant.watering_frequency = str(data["watering_frequency"])[:50]
    if "maintenance_level" in data:
        plant.maintenance_level = str(data["maintenance_level"])[:50]
    if "humidity_requirement" in data:
        plant.humidity_requirement = str(data["humidity_requirement"])[:50]
    if "temperature_range" in data:
        plant.temperature_range = str(data["temperature_range"])[:50]
    if "toxicity_level" in data:
        plant.toxicity_level = str(data["toxicity_level"])[:50]
    if "growth_rate" in data:
        plant.growth_rate = str(data["growth_rate"])[:50]
    if "size_category" in data:
        plant.size_category = str(data["size_category"])[:50]
    if "image_url" in data:
        plant.image_url = str(data["image_url"])[:500] if data["image_url"] else None
    if "category_id" in data:
        try:
            cat = PlantCategory.query.get(int(data["category_id"]))
            if cat:
                plant.category_id = cat.category_id
        except (ValueError, TypeError):
            return jsonify({"error": "category_id must be a number"}), 400
    if "category_name" in data:
        cat_name = str(data["category_name"]).strip()[:100]
        cat = PlantCategory.query.filter_by(category_name=cat_name).first()
        if not cat:
            cat = PlantCategory(category_name=cat_name)
            db.session.add(cat)
            db.session.flush()
        plant.category_id = cat.category_id

    db.session.commit()
    result = plant.to_dict()
    result["category_name"] = plant.category.category_name if plant.category else None
    return jsonify(result), 200


@main.route("/api/plants/<int:plant_id>", methods=["DELETE"])
@admin_required
def delete_plant(plant_id):
    """Delete a plant (admin)."""
    plant = Plant.query.get(plant_id)
    if not plant:
        return jsonify({"error": "Plant not found"}), 404

    db.session.delete(plant)
    db.session.commit()
    return jsonify({"success": True, "message": "Plant deleted"}), 200


# ==========================================
# USER MANAGEMENT ROUTES (admin only)
# ==========================================

@main.route("/api/users", methods=["GET"])
@admin_required
def get_users():
    """Get all users (admin only)."""
    users = User.query.all()
    result = []
    for u in users:
        initials = "".join(w[0].upper() for w in u.name.split()[:2])
        d = u.to_dict()
        d["id"] = d.pop("user_id")
        d["initials"] = initials
        d["role"] = "Admin" if u.is_admin else "Member"
        d["status"] = u.status or "active"
        d["joined"] = u.created_at.strftime("%d %b %Y") if u.created_at else "—"
        d["lastActive"] = "—"
        d["plants"] = 0
        d["bg"] = "#1e1040" if u.is_admin else "#0d2e2e"
        d["fg"] = "#a78bfa" if u.is_admin else "#2dce89"
        result.append(d)
    return jsonify(result), 200


@main.route("/api/users", methods=["POST"])
def create_user():
    """Register a new user (public signup)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required."}), 400
    if len(name) > 100:
        return jsonify({"error": "Name must be under 100 characters."}), 400
    if len(email) > 150:
        return jsonify({"error": "Email must be under 150 characters."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400
    if len(password) > 128:
        return jsonify({"error": "Password must be under 128 characters."}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists."}), 409

    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    new_user = User(
        name=name[:100],
        email=email,
        password=hashed_pw,
        experience_level=data.get("experience_level", "Beginner"),
    )
    db.session.add(new_user)
    db.session.commit()

    session["user_id"] = new_user.user_id
    session.pop("guest_id", None)

    result = new_user.to_dict()
    result["id"] = result.pop("user_id")
    result["initials"] = "".join(w[0].upper() for w in name.split()[:2])
    result["role"] = "Admin" if new_user.is_admin else "Member"
    result["status"] = "active"
    result["joined"] = new_user.created_at.strftime("%d %b %Y") if new_user.created_at else "—"
    result["lastActive"] = "—"
    result["plants"] = 0
    result["bg"] = "#0d2e2e"
    result["fg"] = "#2dce89"
    return jsonify(result), 201


@main.route("/api/users/login", methods=["POST"])
def api_users_login():
    """User login (frontend signin)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Invalid email or password."}), 401

    if not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        return jsonify({"error": "Invalid email or password."}), 401

    if user.status == "suspended":
        return jsonify({"error": "Your account has been suspended."}), 403

    result = user.to_dict()
    result["initials"] = "".join(w[0].upper() for w in user.name.split()[:2])
    result["role"] = "Admin" if user.is_admin else "Member"

    session["user_id"] = user.user_id
    session.pop("guest_id", None)

    return jsonify(result), 200


@main.route("/api/users/<int:user_id>", methods=["PUT"])
@admin_required
def update_user(user_id):
    """Update a user (admin only)."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "name" in data:
        user.name = str(data["name"]).strip()[:100]
    if "email" in data:
        user.email = str(data["email"]).strip().lower()[:150]
    if "experience_level" in data:
        user.experience_level = str(data["experience_level"])[:20]
    if "role" in data:
        user.is_admin = (str(data["role"]).lower() == "admin")
    if "status" in data:
        user.status = str(data["status"])[:20]

    db.session.commit()
    result = user.to_dict()
    result["id"] = result.pop("user_id")
    result["initials"] = "".join(w[0].upper() for w in user.name.split()[:2])
    result["role"] = "Admin" if user.is_admin else "Member"
    return jsonify(result), 200


@main.route("/api/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    """Delete a user (admin only)."""
    if session.get("user_id") == user_id:
        return jsonify({"error": "Cannot delete your own account."}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"success": True}), 200


@main.route("/api/admin/plant-stats", methods=["GET"])
@admin_required
def plant_stats():
    from app.models import Plant

    total = Plant.query.count()

    return jsonify({
        "total_plants": total,
    }), 200


@main.route("/api/dashboard-stats", methods=["GET"])
def dashboard_stats():
    """Return dashboard stats: total plants + user interaction counts."""
    user_id = session.get("user_id")
    total_plants = db.session.query(db.func.count(Plant.plant_id)).scalar() or 0
    searches = 0
    if user_id:
        searches = db.session.query(
            db.func.count(Interaction.interaction_id)
        ).filter(
            Interaction.user_id == user_id,
            Interaction.interaction_type.in_(["View", "Click"])
        ).scalar() or 0
    return jsonify({
        "total_plants": total_plants,
        "searches_run": searches
    })


@main.route("/api/auth/check", methods=["GET"])
def auth_check():
    """Check if current session user is still active."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"authenticated": False}), 200
    user = User.query.get(user_id)
    if not user:
        session.pop("user_id", None)
        return jsonify({"authenticated": False}), 200
    if user.status == "suspended":
        session.pop("user_id", None)
        return jsonify({"authenticated": False, "reason": "suspended"}), 200
    return jsonify({"authenticated": True, "role": "Admin" if user.is_admin else "Member"}), 200


@main.route("/api/feedback", methods=["GET"])
@admin_required
def get_feedback():
    """Get all feedback/reviews (admin only)."""
    from app.models import Review
    from sqlalchemy import desc
    import re

    LABELS = {'Poor': 1, 'Fair': 2, 'Good': 3, 'Very Good': 4, 'Excellent': 5}
    CAT_MAP = {
        'recommendations': 'Plant Recommendations',
        'ui': 'User Interface',
        'accuracy': 'Recommendation Accuracy',
        'feature': 'Feature Request',
        'bug': 'Bug Report',
        'other': 'Other',
    }

    reviews = Review.query.order_by(desc(Review.created_at)).all()
    result = []
    for r in reviews:
        user = User.query.get(r.user_id)
        raw = r.review_text or ''

        cat = '—'
        rating = 0
        comment = raw

        m = re.match(r'^\[Feedback\]\s*(?:\[(\w+)\])?\s*(Poor|Fair|Good|Very Good|Excellent)?\s*:?\s*(.*)', raw)
        if m:
            cat_key = m.group(1)
            rating_label = m.group(2)
            comment = m.group(3).strip() or '—'
            if cat_key:
                cat = CAT_MAP.get(cat_key, cat_key)
            if rating_label:
                rating = LABELS.get(rating_label, 0)

        result.append({
            "id": r.review_id,
            "user_name": user.name if user else "Anonymous",
            "user_email": user.email if user else "—",
            "category": cat,
            "rating": rating,
            "comment": comment,
            "created_at": r.created_at.strftime("%d %b %Y, %H:%M") if r.created_at else "—",
        })
    return jsonify(result), 200


@main.route("/api/feedback", methods=["POST"])
def submit_feedback():
    """Submit feedback (public, no login required)."""
    from app.models import Review
    data = request.get_json()
    if not data or not data.get("text", "").strip():
        return jsonify({"error": "Feedback text is required."}), 400

    text = str(data["text"]).strip()[:2000]
    user_id = session.get("user_id")
    review = Review(
        user_id=user_id,
        plant_id=None,
        review_text="[Feedback] " + text,
    )
    db.session.add(review)
    db.session.commit()
    return jsonify({"success": True}), 201
