# test_main.py
from utils import hash_password, create_access_token, Phone, UserRequest, UserUpdateRequest
import unittest
from datetime import datetime, timezone
import jwt
from pydantic import ValidationError

# Usar la misma clave que en utils.py
TEST_SECRET_KEY = "ejemplo_de_clave_secreta_prueba_tecnica"

class TestHashPassword(unittest.TestCase):
    def test_hash_password_returns_string(self):
        result = hash_password("TestPass123")
        self.assertIsInstance(result, str)
    
    def test_hash_password_different_inputs_different_outputs(self):
        hash1 = hash_password("TestPass123")
        hash2 = hash_password("DifferentPass456")
        self.assertNotEqual(hash1, hash2)
    
    def test_hash_password_not_empty(self):
        result = hash_password("TestPass123")
        self.assertNotEqual(result, "")
        self.assertTrue(len(result) > 10)

class TestCreateAccessToken(unittest.TestCase):
    def test_create_access_token_returns_string(self):
        data = {"user_id": "123", "email": "test@test.com"}
        token = create_access_token(data)
        self.assertIsInstance(token, str)
    
    def test_create_access_token_valid_jwt(self):
        data = {"user_id": "123", "email": "test@test.com"}
        token = create_access_token(data)
        # Verify it's a valid JWT by decoding it
        decoded = jwt.decode(token, TEST_SECRET_KEY, algorithms=["HS256"])
        self.assertEqual(decoded["user_id"], "123")
        self.assertEqual(decoded["email"], "test@test.com")
    
    def test_create_access_token_empty_data(self):
        data = {}
        token = create_access_token(data)
        self.assertIsInstance(token, str)
        decoded = jwt.decode(token, TEST_SECRET_KEY, algorithms=["HS256"])
        self.assertEqual(decoded, {})

class TestPhoneModel(unittest.TestCase):
    def test_phone_valid_data(self):
        phone = Phone(number="123456789", citycode="02", contrycode="+56")
        self.assertEqual(phone.number, "123456789")
        self.assertEqual(phone.citycode, "02")
        self.assertEqual(phone.contrycode, "+56")
    
    def test_phone_string_conversion(self):
        phone = Phone(number="123456789", citycode="02", contrycode="+56")
        phone_dict = phone.model_dump()
        self.assertEqual(phone_dict["number"], "123456789")
        self.assertEqual(phone_dict["citycode"], "02")
        self.assertEqual(phone_dict["contrycode"], "+56")

class TestUserRequestModel(unittest.TestCase):
    def test_user_request_valid_data(self):
        phones = [Phone(number="123456789", citycode="02", contrycode="+56")]
        user = UserRequest(
            name="Test User",
            email="test@domain.cl",
            password="TestPass123",
            phones=phones
        )
        self.assertEqual(user.name, "Test User")
        self.assertEqual(user.email, "test@domain.cl")
        self.assertEqual(user.password, "TestPass123")
        self.assertEqual(len(user.phones), 1)
    
    def test_user_request_invalid_email(self):
        phones = [Phone(number="123456789", citycode="02", contrycode="+56")]
        with self.assertRaises(ValidationError):
            UserRequest(
                name="Test User",
                email="invalid-email",
                password="TestPass123",
                phones=phones
            )
    
    def test_user_request_invalid_password_no_uppercase(self):
        phones = [Phone(number="123456789", citycode="02", contrycode="+56")]
        with self.assertRaises(ValidationError):
            UserRequest(
                name="Test User",
                email="test@domain.cl",
                password="testpass123",  # No uppercase
                phones=phones
            )
    
    def test_user_request_invalid_password_no_numbers(self):
        phones = [Phone(number="123456789", citycode="02", contrycode="+56")]
        with self.assertRaises(ValidationError):
            UserRequest(
                name="Test User",
                email="test@domain.cl",
                password="TestPassword",  # No numbers
                phones=phones
            )
    
    def test_user_request_invalid_password_only_one_number(self):
        phones = [Phone(number="123456789", citycode="02", contrycode="+56")]
        with self.assertRaises(ValidationError):
            UserRequest(
                name="Test User",
                email="test@domain.cl",
                password="TestPass1",  # Only one number
                phones=phones
            )
    
    def test_user_request_valid_password_two_numbers(self):
        phones = [Phone(number="123456789", citycode="02", contrycode="+56")]
        user = UserRequest(
            name="Test User",
            email="test@domain.cl",
            password="TestPass12",  # Two numbers
            phones=phones
        )
        self.assertEqual(user.password, "TestPass12")

class TestUserUpdateRequestModel(unittest.TestCase):
    def test_user_update_request_partial_data(self):
        user_update = UserUpdateRequest(name="Updated Name")
        self.assertEqual(user_update.name, "Updated Name")
        self.assertIsNone(user_update.email)
        self.assertIsNone(user_update.password)
        self.assertIsNone(user_update.phones)
    
    def test_user_update_request_invalid_email(self):
        with self.assertRaises(ValidationError):
            UserUpdateRequest(email="invalid-email")
    
    def test_user_update_request_invalid_password(self):
        with self.assertRaises(ValidationError):
            UserUpdateRequest(password="invalid")
    
    def test_user_update_request_all_none(self):
        user_update = UserUpdateRequest()
        self.assertIsNone(user_update.name)
        self.assertIsNone(user_update.email)
        self.assertIsNone(user_update.password)
        self.assertIsNone(user_update.phones)
    
    def test_user_update_request_only_phones(self):
        phones = [Phone(number="987654321", citycode="09", contrycode="+57")]
        user_update = UserUpdateRequest(phones=phones)
        self.assertIsNone(user_update.name)
        self.assertIsNone(user_update.email)
        self.assertIsNone(user_update.password)
        self.assertEqual(len(user_update.phones), 1)
        self.assertEqual(user_update.phones[0].number, "987654321")

if __name__ == '__main__':
    unittest.main()
