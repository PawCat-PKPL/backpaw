import json
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from user.models import CustomUser
from authentication.models import PaymentMethod, BankDetail

class TestUserProfile(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="user@example.com",
            username="user", 
            password="password")
        
        self.payment = PaymentMethod.objects.create(
        user=self.user, payment_type="gopay", account_number="111111"
    )
        
        self.profile_url = reverse("user:user_profile")
        self.payment_url = reverse("user:payment_method")
        self.bank_create_url = reverse("user:bank_detail_create")
        self.bank_delete_url = lambda bank_name: reverse("user:bank_detail_delete", args=[bank_name])

        self.client.force_authenticate(user=self.user)

    # UserProfileView Tests
    def test_get_user_profile(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "User profile retrieved")

    def test_patch_update_profile_success(self):
        data = {"full_name": "John Doe", "bio": "Hello, I love coding!", "avatar_id": "123"}
        response = self.client.patch(self.profile_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Profile updated successfully")

    def test_patch_update_profile_long_name(self):
        data = {"full_name": "A" * 256}
        response = self.client.patch(self.profile_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Full name is too long")

    def test_patch_update_profile_long_bio(self):
        data = {"bio": "B" * 501}
        response = self.client.patch(self.profile_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Bio is too long")

    # PaymentMethodView Tests
    def test_create_payment_method_success(self):
        data = {"payment_type": "ovo", "account_number": "123456789"}
        response = self.client.post(self.payment_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Payment method added")

    def test_update_existing_payment_method(self):
        PaymentMethod.objects.create(user=self.user, payment_type="credit_card", account_number="111111")
        data = {"payment_type": "gopay", "account_number": "222222"}
        response = self.client.post(self.payment_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Payment method updated")

    def test_create_payment_method_missing_fields(self):
        data = {"payment_type": "credit_card"}
        response = self.client.post(self.payment_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Payment type and account number are required")

    def test_create_payment_method_invalid_type(self):
        data = {"payment_type": "cash", "account_number": "123456"}
        response = self.client.post(self.payment_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Invalid payment type")

    # BankDetailView Tests
    def test_create_bank_detail_success(self):
        data = {"bank_name": "Bank ABC", "account_number": "123456789"}
        response = self.client.post(self.bank_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Bank account added")

    def test_update_existing_bank_detail(self):
        BankDetail.objects.create(user=self.user, bank_name="Bank ABC", account_number="111111")
        data = {"bank_name": "Bank ABC", "account_number": "222222"}
        response = self.client.post(self.bank_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Bank account updated")

    def test_create_bank_detail_missing_fields(self):
        data = {"bank_name": "Bank ABC"}
        response = self.client.post(self.bank_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Bank name and account number are required")

    def test_delete_bank_detail_success(self):
        BankDetail.objects.create(user=self.user, bank_name="Bank XYZ", account_number="555555")
        response = self.client.delete(self.bank_delete_url("Bank XYZ"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Bank account removed")

    def test_delete_bank_detail_not_found(self):
        response = self.client.delete(self.bank_delete_url("Nonexistent Bank"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "Bank account not found")

    # OWASP Testing
    def test_authentication_bypass(self):
        # Tes bypass autentikasi
        # OWASP A1: Broken Authentication
        self.client.force_authenticate(user=None)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_xss_in_profile_data(self):
        # Tes cross site scripting/XSS attack
        # OWASP A2: Cryptographic Failures
        xss_payload = "<script>alert('XSS')</script>"
        data = {"bio": xss_payload}
        response = self.client.patch(self.profile_url, data)
        get_response = self.client.get(self.profile_url)
        self.assertNotIn(xss_payload, str(get_response.content))

    def test_sensitive_data_exposure(self):
        # Tes jika data sensitif terekspos
        # OWASP A3: Sensitive Data Exposure
        self.client.post(self.payment_url, {"payment_type": "credit_card", "account_number": "4111111111111111"})
        response = self.client.get(self.profile_url)
        response_str = json.dumps(response.data)
        self.assertNotIn("4111111111111111", response_str)

    def test_xxe_attack(self):
        # Tes XML External Entity (XXE)
        # OWASP A4: Insecure Design
        xxe_payload = """<?xml version="1.0" encoding="ISO-8859-1"?>
        <!DOCTYPE foo [
        <!ELEMENT foo ANY >
        <!ENTITY xxe SYSTEM "file:///etc/passwd" >]>
        <foo>&xxe;</foo>"""
        headers = {'Content-Type': 'application/xml'}
        response = self.client.post(self.bank_create_url, data=xxe_payload, content_type='application/xml')
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

    def test_broken_access_control(self):
        # Tes seorang user mencoba mengakses data pengguna lain
        # OWASP A5: Broken Access Control
        other_user = CustomUser.objects.create_user(
            email="other@example.com", username="other_user", password="password123")
        BankDetail.objects.create(user=other_user, bank_name="Other Bank", account_number="999999")
        response = self.client.delete(self.bank_delete_url("Other Bank"))
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(BankDetail.objects.filter(user=other_user, bank_name="Other Bank").exists())

    def test_security_misconfiguration(self):
        # Tes miskonfigurasi keamanan dengan mengirim malformed data
        # OWASP A6: Security Misconfiguration
        malformed_data = {"payment_type": "invalid", "account_number": "invalid"}
        response = self.client.post(self.payment_url, malformed_data, format='json')
        response_str = str(response.content)
        self.assertNotIn("Traceback", response_str)
        self.assertNotIn("Django", response_str)

    def test_sql_injection_attack(self):
        # Tes simulasi injeksi SQL
        # OWASP A7: Injection
        sql_injection = "Bank'; DROP TABLE authentication_bankdetail; --"
        response = self.client.post(self.bank_create_url, {"bank_name": sql_injection, "account_number": "123456"})
        try:
            post_injection = self.client.post(self.bank_create_url, {"bank_name": "Legitimate Bank", "account_number": "111222"})
            self.assertEqual(post_injection.status_code, status.HTTP_200_OK)
        except:
            self.fail("SQL injection may have succeeded - database operation failed")

    def test_insecure_deserialization(self):
        # Tes simulasi deserialisasi yang tidak aman
        # OWASP A8: Insecure Deserialization
        malformed_data = {
            "full_name": "__dict__.update({'is_admin': True})",
            "bio": "Testing insecure deserialization"
        }
        response = self.client.patch(self.profile_url, malformed_data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_component_vulnerabilities(self):
        # Tes vulnerabilitas komponen
        # OWASP A9: Vulnerable and Outdated Components
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_insufficient_logging_monitoring(self):
        # Tes apakah sudah ada logging yang memadai
        # OWASP A10: Insufficient Logging & Monitoring
        self.client.force_authenticate(user=None)
        invalid_data = {"payment_type": "hacked", "account_number": "malicious"}
        response = self.client.post(self.payment_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
