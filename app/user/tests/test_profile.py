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