import unittest
from fastapi import HTTPException

# Import the application elements directly from main
from main import (
    register,
    login,
    list_courses,
    view_course,
    RegisterSchema,
    LoginSchema,
    users_db,
    sessions_db,
    get_current_user,
    COURSES
)

class TestAgentEducationSystem(unittest.TestCase):
    def setUp(self):
        # Clear database states for clean test run
        users_db.clear()
        sessions_db.clear()

    def test_user_registration_and_duplicate_check(self):
        # 1. Register a new user
        reg_data = RegisterSchema(email="student@test.com", password="SecurePassword123!")
        res = register(reg_data)
        self.assertEqual(res["email"], "student@test.com")
        self.assertIn("student@test.com", users_db)
        
        # Verify password is hashed (should not equal the plain text)
        hashed_pw = users_db["student@test.com"]
        self.assertNotEqual(hashed_pw, "SecurePassword123!")
        
        # 2. Try to register the same user again
        with self.assertRaises(HTTPException) as ctx:
            register(reg_data)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("already exists", ctx.exception.detail)

    def test_user_login(self):
        # Register first
        reg_data = RegisterSchema(email="user@test.com", password="SecretPassword!")
        register(reg_data)

        # 1. Login with correct credentials
        login_data = LoginSchema(email="user@test.com", password="SecretPassword!")
        res = login(login_data)
        self.assertEqual(res["email"], "user@test.com")
        self.assertIsNotNone(res["session_token"])
        
        # Verify token is in sessions_db
        token = res["session_token"]
        self.assertEqual(sessions_db[token], "user@test.com")

        # 2. Login with incorrect password
        bad_login_data = LoginSchema(email="user@test.com", password="WrongPassword")
        with self.assertRaises(HTTPException) as ctx:
            login(bad_login_data)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_authentication_dependency(self):
        # 1. Test missing authorization header
        with self.assertRaises(HTTPException) as ctx:
            get_current_user(None)
        self.assertEqual(ctx.exception.status_code, 401)

        # 2. Test invalid authorization scheme
        with self.assertRaises(HTTPException) as ctx:
            get_current_user("Basic token123")
        self.assertEqual(ctx.exception.status_code, 401)

        # 3. Test invalid token value
        with self.assertRaises(HTTPException) as ctx:
            get_current_user("Bearer invalid_token")
        self.assertEqual(ctx.exception.status_code, 401)

        # 4. Test valid token
        sessions_db["test_token"] = "auth_user@test.com"
        user = get_current_user("Bearer test_token")
        self.assertEqual(user, "auth_user@test.com")

    def test_courses_endpoints(self):
        # 1. Verify list_courses returns expected list
        courses = list_courses("test_user@test.com")
        self.assertEqual(len(courses), 2)
        self.assertEqual(courses[0]["id"], "corporate-tesco")
        self.assertEqual(courses[1]["id"], "academic-ai")

        # 2. Verify view_course returns details for corporate
        corp_course = view_course("corporate-tesco", "test_user@test.com")
        self.assertEqual(corp_course["title"], COURSES["corporate-tesco"]["title"])
        self.assertEqual(len(corp_course["lessons"]), 2)

        # 3. Verify view_course returns details for academic
        acad_course = view_course("academic-ai", "test_user@test.com")
        self.assertEqual(acad_course["title"], COURSES["academic-ai"]["title"])
        self.assertEqual(len(acad_course["lessons"]), 2)

        # 4. Verify view_course raises 404 for invalid ID
        with self.assertRaises(HTTPException) as ctx:
            view_course("invalid-course-id", "test_user@test.com")
        self.assertEqual(ctx.exception.status_code, 404)

if __name__ == "__main__":
    unittest.main()
