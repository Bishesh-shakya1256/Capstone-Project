"""
test_database.py - Comprehensive Test Suite for Plant Recommendation System
Tests all database operations, API routes, models, and recommendation engine.

Run: python -m pytest tests/test_database.py -v
"""

import pytest
import sys
import os
import bcrypt
import json
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import db, User, Guest, Plant, PlantCategory, UserPreference, \
    Environment, Interaction, Rating, Review, Recommendation


# ─── FIXTURES ────────────────────────────────────────────────────────────────

@pytest.fixture
def app():
    """Create a test app with an in-memory SQLite database."""
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seed_data(app):
    """Seed minimum data needed for tests."""
    with app.app_context():
        cat = PlantCategory.query.filter_by(category_name="General").first()
        if not cat:
            cat = PlantCategory(category_name="General")
            db.session.add(cat)
            db.session.flush()

        plants = [
            Plant(plant_name="Aloe Vera", category_id=cat.category_id,
                  light_requirement="High", watering_frequency="Weekly",
                  maintenance_level="Medium", humidity_requirement="Low",
                  temperature_range="Warm", toxicity_level="Non-toxic",
                  growth_rate="Slow", size_category="Medium"),
            Plant(plant_name="Snake Plant", category_id=cat.category_id,
                  light_requirement="Low", watering_frequency="Bi-weekly",
                  maintenance_level="Low", humidity_requirement="Low",
                  temperature_range="Moderate", toxicity_level="Toxic",
                  growth_rate="Slow", size_category="Large"),
            Plant(plant_name="Pothos", category_id=cat.category_id,
                  light_requirement="Medium", watering_frequency="Weekly",
                  maintenance_level="Low", humidity_requirement="Medium",
                  temperature_range="Moderate", toxicity_level="Toxic",
                  growth_rate="Fast", size_category="Small"),
            Plant(plant_name="Peace Lily", category_id=cat.category_id,
                  light_requirement="Low", watering_frequency="Weekly",
                  maintenance_level="Medium", humidity_requirement="High",
                  temperature_range="Moderate", toxicity_level="Toxic",
                  growth_rate="Moderate", size_category="Medium"),
            Plant(plant_name="Monstera", category_id=cat.category_id,
                  light_requirement="Medium", watering_frequency="Weekly",
                  maintenance_level="Medium", humidity_requirement="High",
                  temperature_range="Moderate", toxicity_level="Toxic",
                  growth_rate="Fast", size_category="Large"),
        ]
        db.session.add_all(plants)
        db.session.commit()

        plant_ids = [p.plant_id for p in Plant.query.all()]
        return {"cat_id": cat.category_id, "plant_ids": plant_ids}


@pytest.fixture
def seed_user(app):
    """Create a test user."""
    with app.app_context():
        hashed = bcrypt.hashpw(b"test123", bcrypt.gensalt()).decode("utf-8")
        user = User(name="Test User", email="test@test.com",
                    password=hashed, experience_level="Beginner")
        db.session.add(user)
        db.session.commit()
        return {"user_id": user.user_id, "email": "test@test.com", "password": "test123"}


@pytest.fixture
def seed_admin(app):
    """Create a test admin user."""
    with app.app_context():
        hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")
        admin = User(name="Test Admin", email="admin@test.com",
                     password=hashed, experience_level="Beginner", is_admin=True)
        db.session.add(admin)
        db.session.commit()
        return {"user_id": admin.user_id, "email": "admin@test.com", "password": "admin123"}


@pytest.fixture
def seed_guest(app):
    """Create a test guest."""
    with app.app_context():
        guest = Guest(session_id="test-uuid-123")
        db.session.add(guest)
        db.session.commit()
        return {"guest_id": guest.guest_id}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: USER MANAGEMENT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegisterUser:
    def test_register_success(self, app, seed_data):
        from app.db_utils import register_user
        with app.app_context():
            result = register_user("John", "john@test.com", "pass123", "Beginner")
            assert result["success"] is True
            assert "user_id" in result

    def test_register_duplicate_email(self, app, seed_data, seed_user):
        from app.db_utils import register_user
        with app.app_context():
            result = register_user("Another", "test@test.com", "pass123", "Expert")
            assert result["success"] is False
            assert "already" in result["error"].lower() or "registered" in result["error"].lower()

    def test_register_invalid_experience(self, app, seed_data):
        from app.db_utils import register_user
        with app.app_context():
            result = register_user("John", "john@test.com", "pass123", "InvalidLevel")
            assert result["success"] is False
            assert "experience_level" in result["error"]

    def test_register_email_normalized(self, app, seed_data):
        from app.db_utils import register_user
        with app.app_context():
            result = register_user("John", "  JOHN@Test.COM  ", "pass123", "Beginner")
            assert result["success"] is True
            user = User.query.get(result["user_id"])
            assert user.email == "john@test.com"

    def test_register_password_stored_hashed(self, app, seed_data):
        from app.db_utils import register_user
        with app.app_context():
            result = register_user("John", "john@test.com", "pass123", "Beginner")
            user = User.query.get(result["user_id"])
            assert user.password != "pass123"
            assert bcrypt.checkpw(b"pass123", user.password.encode("utf-8"))


class TestLoginUser:
    def test_login_success(self, app, seed_user):
        from app.db_utils import login_user
        with app.app_context():
            result = login_user("test@test.com", "test123")
            assert result["success"] is True
            assert result["user"]["name"] == "Test User"

    def test_login_wrong_password(self, app, seed_user):
        from app.db_utils import login_user
        with app.app_context():
            result = login_user("test@test.com", "wrongpassword")
            assert result["success"] is False
            assert "password" in result["error"].lower()

    def test_login_nonexistent_email(self, app, seed_data):
        from app.db_utils import login_user
        with app.app_context():
            result = login_user("nobody@test.com", "pass123")
            assert result["success"] is False
            assert "not found" in result["error"].lower()

    def test_login_case_insensitive_email(self, app, seed_user):
        from app.db_utils import login_user
        with app.app_context():
            result = login_user("TEST@TEST.COM", "test123")
            assert result["success"] is True


class TestGuestSession:
    def test_create_guest(self, app):
        from app.db_utils import create_guest_session
        with app.app_context():
            result = create_guest_session()
            assert result["success"] is True
            assert "guest_id" in result
            assert "session_id" in result

    def test_guest_session_uuid_unique(self, app):
        from app.db_utils import create_guest_session
        with app.app_context():
            r1 = create_guest_session()
            r2 = create_guest_session()
            assert r1["session_id"] != r2["session_id"]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: USER PREFERENCES TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestUserPreferences:
    def test_save_preference_success(self, app, seed_user):
        from app.db_utils import save_user_preference
        with app.app_context():
            result = save_user_preference(seed_user["user_id"], "High", "Low", "Small", True)
            assert result["success"] is True
            pref = UserPreference.query.filter_by(user_id=seed_user["user_id"]).first()
            assert pref.preferred_light == "High"
            assert pref.preferred_maintenance == "Low"
            assert pref.preferred_size == "Small"
            assert pref.pet_friendly_required is True

    def test_save_preference_replaces_old(self, app, seed_user):
        from app.db_utils import save_user_preference
        with app.app_context():
            save_user_preference(seed_user["user_id"], "High", "Low", "Small", False)
            save_user_preference(seed_user["user_id"], "Low", "High", "Large", True)
            prefs = UserPreference.query.filter_by(user_id=seed_user["user_id"]).all()
            assert len(prefs) == 1
            assert prefs[0].preferred_light == "Low"

    def test_save_preference_invalid_user(self, app, seed_data):
        from app.db_utils import save_user_preference
        with app.app_context():
            result = save_user_preference(9999, "High", "Low", "Small", False)
            assert result["success"] is False

    def test_save_preference_invalid_light(self, app, seed_user):
        from app.db_utils import save_user_preference
        with app.app_context():
            result = save_user_preference(seed_user["user_id"], "Invalid", "Low", "Small", False)
            assert result["success"] is False
            assert "preferred_light" in result["error"]

    def test_save_preference_invalid_size(self, app, seed_user):
        from app.db_utils import save_user_preference
        with app.app_context():
            result = save_user_preference(seed_user["user_id"], "High", "Low", "Invalid", False)
            assert result["success"] is False
            assert "preferred_size" in result["error"]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: ENVIRONMENT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestEnvironment:
    def test_save_environment_success(self, app, seed_user):
        from app.db_utils import save_environment
        with app.app_context():
            result = save_environment(seed_user["user_id"], "High", "Medium", "Warm", "Small")
            assert result["success"] is True
            env = Environment.query.filter_by(user_id=seed_user["user_id"]).first()
            assert env.light_level == "High"
            assert env.room_size == "Small"

    def test_save_multiple_environments(self, app, seed_user):
        from app.db_utils import save_environment
        with app.app_context():
            save_environment(seed_user["user_id"], "High", "Medium", "Warm", "Small")
            save_environment(seed_user["user_id"], "Low", "High", "Cool", "Large")
            envs = Environment.query.filter_by(user_id=seed_user["user_id"]).all()
            assert len(envs) == 2

    def test_save_environment_invalid_temperature(self, app, seed_user):
        from app.db_utils import save_environment
        with app.app_context():
            result = save_environment(seed_user["user_id"], "High", "Medium", "Hot", "Small")
            assert result["success"] is False
            assert "temperature" in result["error"]

    def test_save_environment_invalid_user(self, app, seed_data):
        from app.db_utils import save_environment
        with app.app_context():
            result = save_environment(9999, "High", "Medium", "Warm", "Small")
            assert result["success"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: INTERACTION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestInteraction:
    def test_log_interaction_user(self, app, seed_user, seed_data):
        from app.db_utils import log_interaction
        with app.app_context():
            pid = seed_data["plant_ids"][0]
            result = log_interaction(pid, "View", user_id=seed_user["user_id"])
            assert result["success"] is True
            assert Interaction.query.count() == 1

    def test_log_interaction_guest(self, app, seed_guest, seed_data):
        from app.db_utils import log_interaction
        with app.app_context():
            pid = seed_data["plant_ids"][0]
            result = log_interaction(pid, "Click", guest_id=seed_guest["guest_id"])
            assert result["success"] is True

    def test_log_interaction_invalid_type(self, app, seed_user, seed_data):
        from app.db_utils import log_interaction
        with app.app_context():
            pid = seed_data["plant_ids"][0]
            result = log_interaction(pid, "Invalid", user_id=seed_user["user_id"])
            assert result["success"] is False
            assert "interaction_type" in result["error"]

    def test_log_interaction_no_identity(self, app, seed_data):
        from app.db_utils import log_interaction
        with app.app_context():
            pid = seed_data["plant_ids"][0]
            result = log_interaction(pid, "View")
            assert result["success"] is False

    def test_log_interaction_invalid_plant(self, app, seed_user):
        from app.db_utils import log_interaction
        with app.app_context():
            result = log_interaction(9999, "View", user_id=seed_user["user_id"])
            assert result["success"] is False
            assert "plant" in result["error"].lower()

    def test_log_all_interaction_types(self, app, seed_user, seed_data):
        from app.db_utils import log_interaction
        with app.app_context():
            pid = seed_data["plant_ids"][0]
            for itype in ["View", "Click", "Save", "Share"]:
                result = log_interaction(pid, itype, user_id=seed_user["user_id"])
                assert result["success"] is True
            assert Interaction.query.count() == 4


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: RATING TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestRating:
    def test_submit_rating_success(self, app, seed_user, seed_data):
        from app.db_utils import submit_rating
        with app.app_context():
            pid = seed_data["plant_ids"][0]
            result = submit_rating(seed_user["user_id"], pid, 5)
            assert result["success"] is True
            assert Rating.query.count() == 1

    def test_submit_rating_update_existing(self, app, seed_user, seed_data):
        from app.db_utils import submit_rating
        with app.app_context():
            pid = seed_data["plant_ids"][0]
            submit_rating(seed_user["user_id"], pid, 3)
            submit_rating(seed_user["user_id"], pid, 5)
            ratings = Rating.query.filter_by(user_id=seed_user["user_id"], plant_id=pid).all()
            assert len(ratings) == 1
            assert ratings[0].rating_value == 5

    def test_submit_rating_invalid_value(self, app, seed_user, seed_data):
        from app.db_utils import submit_rating
        with app.app_context():
            pid = seed_data["plant_ids"][0]
            assert submit_rating(seed_user["user_id"], pid, 0)["success"] is False
            assert submit_rating(seed_user["user_id"], pid, 6)["success"] is False
            assert submit_rating(seed_user["user_id"], pid, 3.5)["success"] is False

    def test_submit_rating_boundary_values(self, app, seed_user, seed_data):
        from app.db_utils import submit_rating
        with app.app_context():
            pid = seed_data["plant_ids"][0]
            assert submit_rating(seed_user["user_id"], pid, 1)["success"] is True
            assert submit_rating(seed_user["user_id"], pid, 5)["success"] is True

    def test_submit_rating_invalid_user(self, app, seed_data):
        from app.db_utils import submit_rating
        with app.app_context():
            pid = seed_data["plant_ids"][0]
            result = submit_rating(9999, pid, 4)
            assert result["success"] is False

    def test_submit_rating_invalid_plant(self, app, seed_user):
        from app.db_utils import submit_rating
        with app.app_context():
            result = submit_rating(seed_user["user_id"], 9999, 4)
            assert result["success"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: REVIEW TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestReview:
    def test_submit_review_success(self, app, seed_user, seed_data):
        from app.db_utils import submit_review
        with app.app_context():
            pid = seed_data["plant_ids"][0]
            result = submit_review(seed_user["user_id"], pid, "Great plant!")
            assert result["success"] is True
            assert Review.query.count() == 1

    def test_submit_review_empty_text(self, app, seed_user, seed_data):
        from app.db_utils import submit_review
        with app.app_context():
            pid = seed_data["plant_ids"][0]
            assert submit_review(seed_user["user_id"], pid, "")["success"] is False
            assert submit_review(seed_user["user_id"], pid, "   ")["success"] is False

    def test_submit_review_text_stripped(self, app, seed_user, seed_data):
        from app.db_utils import submit_review
        with app.app_context():
            pid = seed_data["plant_ids"][0]
            result = submit_review(seed_user["user_id"], pid, "  Nice plant  ")
            assert result["success"] is True
            review = Review.query.get(result["review_id"])
            assert review.review_text == "Nice plant"

    def test_submit_review_multiple_per_user(self, app, seed_user, seed_data):
        from app.db_utils import submit_review
        with app.app_context():
            pid = seed_data["plant_ids"][0]
            submit_review(seed_user["user_id"], pid, "First review")
            submit_review(seed_user["user_id"], pid, "Second review")
            assert Review.query.count() == 2

    def test_submit_review_invalid_user(self, app, seed_data):
        from app.db_utils import submit_review
        with app.app_context():
            pid = seed_data["plant_ids"][0]
            result = submit_review(9999, pid, "Nice")
            assert result["success"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7: PLANT CRUD TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPlantRetrieval:
    def test_get_all_plants(self, app, seed_data):
        from app.db_utils import get_all_plants
        with app.app_context():
            result = get_all_plants()
            assert result["success"] is True
            assert len(result["plants"]) == 5

    def test_get_plant_by_id(self, app, seed_data):
        from app.db_utils import get_plant_by_id
        with app.app_context():
            pid = seed_data["plant_ids"][0]
            result = get_plant_by_id(pid)
            assert result["success"] is True
            assert result["plant"]["plant_name"] == "Aloe Vera"

    def test_get_plant_not_found(self, app, seed_data):
        from app.db_utils import get_plant_by_id
        with app.app_context():
            result = get_plant_by_id(9999)
            assert result["success"] is False

    def test_plant_has_category_name(self, app, seed_data):
        from app.db_utils import get_all_plants
        with app.app_context():
            result = get_all_plants()
            for p in result["plants"]:
                assert "category_name" in p


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8: RECOMMENDATION ENGINE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestCFRecommendation:
    def test_cf_with_no_ratings_fallback(self, app, seed_user, seed_data):
        from app.db_utils import generate_cf_recommendation
        with app.app_context():
            result = generate_cf_recommendation(seed_user["user_id"])
            assert result["success"] is True
            assert len(result["recommendations"]) > 0

    def test_cf_with_ratings(self, app, seed_user, seed_data):
        from app.db_utils import generate_cf_recommendation, submit_rating
        with app.app_context():
            for pid in seed_data["plant_ids"][:3]:
                submit_rating(seed_user["user_id"], pid, 4)
            result = generate_cf_recommendation(seed_user["user_id"])
            assert result["success"] is True

    def test_cf_stores_recommendations(self, app, seed_user, seed_data):
        from app.db_utils import generate_cf_recommendation
        with app.app_context():
            generate_cf_recommendation(seed_user["user_id"])
            recs = Recommendation.query.filter_by(user_id=seed_user["user_id"]).all()
            assert len(recs) > 0

    def test_cf_clears_old_recommendations(self, app, seed_user, seed_data):
        from app.db_utils import generate_cf_recommendation
        with app.app_context():
            generate_cf_recommendation(seed_user["user_id"])
            count1 = Recommendation.query.filter_by(user_id=seed_user["user_id"]).count()
            generate_cf_recommendation(seed_user["user_id"])
            count2 = Recommendation.query.filter_by(user_id=seed_user["user_id"]).count()
            assert count1 == count2

    def test_cf_invalid_user(self, app, seed_data):
        from app.db_utils import generate_cf_recommendation
        with app.app_context():
            result = generate_cf_recommendation(9999)
            assert result["success"] is False


class TestGuestRecommendation:
    def test_guest_recommendation_cold_start(self, app, seed_guest, seed_data):
        from app.db_utils import generate_guest_recommendation
        with app.app_context():
            result = generate_guest_recommendation(seed_guest["guest_id"])
            assert result["success"] is True
            assert len(result["recommendations"]) > 0

    def test_guest_recommendation_stores(self, app, seed_guest, seed_data):
        from app.db_utils import generate_guest_recommendation
        with app.app_context():
            generate_guest_recommendation(seed_guest["guest_id"])
            recs = Recommendation.query.filter_by(guest_id=seed_guest["guest_id"]).all()
            assert len(recs) > 0

    def test_guest_recommendation_invalid_guest(self, app, seed_data):
        from app.db_utils import generate_guest_recommendation
        with app.app_context():
            result = generate_guest_recommendation(9999)
            assert result["success"] is False

    def test_guest_recommendation_with_ratings(self, app, seed_guest, seed_data):
        from app.db_utils import generate_guest_recommendation, submit_rating
        with app.app_context():
            user = User(name="Rater", email="rater@test.com",
                        password="x", experience_level="Beginner")
            db.session.add(user)
            db.session.flush()
            for pid in seed_data["plant_ids"]:
                submit_rating(user.user_id, pid, 5)
            result = generate_guest_recommendation(seed_guest["guest_id"])
            assert result["success"] is True
            assert result["algorithm"] == "CF"


class TestGetRecommendations:
    def test_get_recs_for_user(self, app, seed_user, seed_data):
        from app.db_utils import generate_cf_recommendation, get_recommendations
        with app.app_context():
            generate_cf_recommendation(seed_user["user_id"])
            result = get_recommendations(user_id=seed_user["user_id"])
            assert result["success"] is True
            assert len(result["recommendations"]) > 0

    def test_get_recs_for_guest(self, app, seed_guest, seed_data):
        from app.db_utils import generate_guest_recommendation, get_recommendations
        with app.app_context():
            generate_guest_recommendation(seed_guest["guest_id"])
            result = get_recommendations(guest_id=seed_guest["guest_id"])
            assert result["success"] is True

    def test_get_recs_no_identity(self, app):
        from app.db_utils import get_recommendations
        with app.app_context():
            result = get_recommendations()
            assert result["success"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 9: MODEL / TO_DICT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestModels:
    def test_user_to_dict(self, app, seed_user):
        with app.app_context():
            user = User.query.get(seed_user["user_id"])
            d = user.to_dict()
            assert d["name"] == "Test User"
            assert "password" not in d

    def test_guest_to_dict(self, app, seed_guest):
        with app.app_context():
            guest = Guest.query.get(seed_guest["guest_id"])
            d = guest.to_dict()
            assert "session_id" in d

    def test_plant_to_dict(self, app, seed_data):
        with app.app_context():
            plant = Plant.query.first()
            d = plant.to_dict()
            assert "plant_name" in d
            assert "light_requirement" in d

    def test_category_to_dict(self, app, seed_data):
        with app.app_context():
            cat = PlantCategory.query.first()
            d = cat.to_dict()
            assert d["category_name"] == "General"

    def test_preference_to_dict(self, app, seed_user):
        from app.db_utils import save_user_preference
        with app.app_context():
            save_user_preference(seed_user["user_id"], "High", "Low", "Small", True)
            pref = UserPreference.query.first()
            d = pref.to_dict()
            assert d["preferred_light"] == "High"

    def test_environment_to_dict(self, app, seed_user):
        from app.db_utils import save_environment
        with app.app_context():
            save_environment(seed_user["user_id"], "High", "Medium", "Warm", "Small")
            env = Environment.query.first()
            d = env.to_dict()
            assert d["light_level"] == "High"

    def test_rating_to_dict(self, app, seed_user, seed_data):
        from app.db_utils import submit_rating
        with app.app_context():
            submit_rating(seed_user["user_id"], seed_data["plant_ids"][0], 4)
            rating = Rating.query.first()
            d = rating.to_dict()
            assert d["rating_value"] == 4

    def test_review_to_dict(self, app, seed_user, seed_data):
        from app.db_utils import submit_review
        with app.app_context():
            submit_review(seed_user["user_id"], seed_data["plant_ids"][0], "Nice")
            review = Review.query.first()
            d = review.to_dict()
            assert d["review_text"] == "Nice"


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 10: API ROUTE TESTS (HTTP)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAPIRoutes:
    def test_get_plants(self, client, seed_data):
        resp = client.get("/api/plants")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["plants"]) == 5

    def test_get_plant_by_id(self, client, seed_data):
        pid = seed_data["plant_ids"][0]
        resp = client.get(f"/api/plants/{pid}")
        assert resp.status_code == 200

    def test_get_plant_not_found(self, client, seed_data):
        resp = client.get("/api/plants/9999")
        assert resp.status_code == 404

    def test_register_route(self, client, seed_data):
        resp = client.post("/api/users", json={
            "name": "API User",
            "email": "api@test.com",
            "password": "pass123",
            "experience_level": "Beginner"
        })
        assert resp.status_code == 201

    def test_login_route(self, client, seed_user):
        resp = client.post("/api/users/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        assert resp.status_code == 200

    def test_login_wrong_password_route(self, client, seed_user):
        resp = client.post("/api/users/login", json={
            "email": "test@test.com",
            "password": "wrong"
        })
        assert resp.status_code == 401

    def test_rate_route(self, client, seed_user, seed_data):
        with client.session_transaction() as sess:
            sess["user_id"] = seed_user["user_id"]
        pid = seed_data["plant_ids"][0]
        resp = client.post("/api/rate", json={
            "plant_id": pid,
            "rating_value": 4
        })
        assert resp.status_code == 200

    def test_review_route(self, client, seed_user, seed_data):
        with client.session_transaction() as sess:
            sess["user_id"] = seed_user["user_id"]
        pid = seed_data["plant_ids"][0]
        resp = client.post("/api/review", json={
            "plant_id": pid,
            "review_text": "Great plant!"
        })
        assert resp.status_code == 201

    def test_interact_route(self, client, seed_user, seed_data):
        with client.session_transaction() as sess:
            sess["user_id"] = seed_user["user_id"]
        pid = seed_data["plant_ids"][0]
        resp = client.post("/api/interact", json={
            "plant_id": pid,
            "interaction_type": "View"
        })
        assert resp.status_code == 201

    def test_home_page(self, client, seed_data):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_recommendations_page(self, client, seed_data):
        resp = client.get("/recommendations.html")
        assert resp.status_code == 200

    def test_create_plant_route(self, client, seed_admin, seed_data):
        with client.session_transaction() as sess:
            sess["user_id"] = seed_admin["user_id"]
        resp = client.post("/api/plants", json={
            "plant_name": "Test Fern",
            "category_name": "General",
            "light_requirement": "Low",
            "watering_frequency": "Weekly",
            "maintenance_level": "Low",
            "humidity_requirement": "High",
            "temperature_range": "Moderate",
            "toxicity_level": "Non-toxic",
            "growth_rate": "Moderate",
            "size_category": "Small"
        })
        assert resp.status_code == 201

    def test_update_plant_route(self, client, seed_admin, seed_data):
        with client.session_transaction() as sess:
            sess["user_id"] = seed_admin["user_id"]
        pid = seed_data["plant_ids"][0]
        resp = client.put(f"/api/plants/{pid}", json={
            "plant_name": "Updated Aloe"
        })
        assert resp.status_code == 200

    def test_delete_plant_route(self, client, seed_admin, seed_data):
        with client.session_transaction() as sess:
            sess["user_id"] = seed_admin["user_id"]
        pid = seed_data["plant_ids"][4]
        resp = client.delete(f"/api/plants/{pid}")
        assert resp.status_code == 200

    def test_get_users_route(self, client, seed_admin):
        with client.session_transaction() as sess:
            sess["user_id"] = seed_admin["user_id"]
        resp = client.get("/api/users")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 11: EDGE CASE & INTEGRITY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_cascade_delete_user_deletes_prefs(self, app, seed_user):
        from app.db_utils import save_user_preference
        with app.app_context():
            save_user_preference(seed_user["user_id"], "High", "Low", "Small", False)
            user = User.query.get(seed_user["user_id"])
            db.session.delete(user)
            db.session.commit()
            assert UserPreference.query.filter_by(user_id=seed_user["user_id"]).count() == 0

    def test_cascade_delete_plant_deletes_ratings(self, app, seed_user, seed_data):
        from app.db_utils import submit_rating
        with app.app_context():
            pid = seed_data["plant_ids"][0]
            submit_rating(seed_user["user_id"], pid, 5)
            plant = Plant.query.get(pid)
            db.session.delete(plant)
            db.session.commit()
            assert Rating.query.filter_by(plant_id=pid).count() == 0

    def test_unique_plant_name_constraint(self, app, seed_data):
        with app.app_context():
            cat = PlantCategory.query.first()
            p = Plant(plant_name="Aloe Vera", category_id=cat.category_id,
                      light_requirement="High", watering_frequency="Weekly",
                      maintenance_level="Medium", humidity_requirement="Low",
                      temperature_range="Warm", toxicity_level="Non-toxic",
                      growth_rate="Slow", size_category="Medium")
            db.session.add(p)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()

    def test_unique_email_constraint(self, app, seed_user):
        with app.app_context():
            u = User(name="Dup", email="test@test.com", password="x",
                     experience_level="Beginner")
            db.session.add(u)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()

    def test_rating_check_constraint(self, app, seed_user, seed_data):
        with app.app_context():
            pid = seed_data["plant_ids"][0]
            r = Rating(user_id=seed_user["user_id"], plant_id=pid, rating_value=10)
            db.session.add(r)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()

    def test_recommendation_ordering(self, app, seed_user, seed_data):
        from app.db_utils import generate_cf_recommendation, get_recommendations
        with app.app_context():
            generate_cf_recommendation(seed_user["user_id"])
            result = get_recommendations(user_id=seed_user["user_id"])
            ranks = [r["rank"] for r in result["recommendations"]]
            assert ranks == sorted(ranks)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
