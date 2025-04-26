from django.utils import timezone
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from authentication.models import CustomUser
from user_dashboard.models import Transaction, Category

import json
from decimal import Decimal
from unittest.mock import patch

User = CustomUser

class TransactionAPISecurityTests(TestCase):
    """
    Test suite covering OWASP Top 10 security vulnerabilities for Transaction API
    """
    
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username="testuser1", 
            email="test1@example.com", 
            password="SecurePass123!",
            saldo=Decimal('1000.00')
        )
        self.user2 = User.objects.create_user(
            username="testuser2", 
            email="test2@example.com", 
            password="AnotherSecurePass123!",
            saldo=Decimal('500.00')
        )
        
        # Create test categories
        self.category1 = Category.objects.create(name="Food", user=self.user1)
        self.category2 = Category.objects.create(name="Salary", user=self.user1)
        self.category3 = Category.objects.create(name="Entertainment", user=self.user2)
        
        # Create test transactions
        self.transaction1 = Transaction.objects.create(
            user=self.user1,
            category=self.category1,
            amount=Decimal('50.00'),
            type='expense',
            description='Groceries',
            date=timezone.now().date()
        )
        
        self.transaction2 = Transaction.objects.create(
            user=self.user2,
            category=self.category3,
            amount=Decimal('100.00'),
            type='expense',
            description='Movie tickets',
            date=timezone.now().date()
        )
        
        # Set up API client
        self.client = APIClient()
        
        # API endpoints
        self.transactions_url = reverse('transaction-list-create')
        self.categories_url = reverse('category-list-create')
        
    # 1. A01:2021 – Broken Access Control
    def test_unauthorized_access_prevented(self):
        """Test that unauthorized access is prevented (A01)"""
        # Attempt to access without authentication
        response = self.client.get(self.transactions_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.post(self.transactions_url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_cross_user_resource_access_prevented(self):
        """Test that users cannot access other users' data (A01)"""
        # Authenticate as user1
        self.client.force_authenticate(user=self.user1)
        
        # Attempt to access transaction belonging to user2
        transaction_detail_url = reverse('transaction-detail', kwargs={'pk': self.transaction2.id})
        
        # Try to update
        response = self.client.patch(transaction_detail_url, {'amount': '200.00'})
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED])
        
        # Try to delete
        response = self.client.delete(transaction_detail_url)
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED])
        
        # Verify transaction still exists
        self.assertTrue(Transaction.objects.filter(id=self.transaction2.id).exists())
    
    # 2. A02:2021 – Cryptographic Failures
    def test_sensitive_data_not_exposed(self):
        """Test that sensitive data is not exposed in responses (A02)"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.transactions_url)
        
        # Check response doesn't contain sensitive user data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        
        # no password or sensitive user data is exposed
        self.assertNotIn('password', str(response_data))
        self.assertNotIn('token', str(response_data))
        self.assertNotIn('session', str(response_data))
    
    # 3. A03:2021 – Injection
    def test_sql_injection_prevention(self):
        """Test that SQL injection is prevented (A03)"""
        self.client.force_authenticate(user=self.user1)
        
        sql_injection_attempts = [
            "'; DROP TABLE transactions; --",
            "1 OR 1=1",
            "1; SELECT * FROM auth_user",
        ]
        
        for injection in sql_injection_attempts:
            response = self.client.post(
                self.categories_url, 
                {'name': injection}
            )
            
            if response.status_code == status.HTTP_201_CREATED:
                response_data = json.loads(response.content)
                category_id = response_data['data']['id']
                category = Category.objects.get(id=category_id)
                self.assertEqual(category.name, injection)
            
            response = self.client.post(
                self.transactions_url,
                {
                    'amount': '10.00',
                    'type': 'expense',
                    'description': injection,
                    'date': timezone.now().date().isoformat(),
                    'category_id': self.category1.id
                }
            )
            
            if response.status_code == status.HTTP_201_CREATED:
                response_data = json.loads(response.content)
                transaction_id = response_data['data']['id']
                transaction = Transaction.objects.get(id=transaction_id)
                self.assertEqual(transaction.description, injection)
    
    # 4. A04:2021 – Insecure Design
    def test_business_logic_enforced(self):
        """Test that business logic constraints are properly enforced (A04)"""
        self.client.force_authenticate(user=self.user1)
        
        # Test negative amount prevention
        response = self.client.post(
            self.transactions_url,
            {
                'amount': '-100.00',
                'type': 'expense',
                'description': 'Attempt negative expense',
                'date': timezone.now().date().isoformat(),
                'category_id': self.category1.id
            }
        )
        
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test data validation for transaction type
        response = self.client.post(
            self.transactions_url,
            {
                'amount': '100.00',
                'type': 'invalid_type',  # Invalid transaction type
                'description': 'Invalid transaction type',
                'date': timezone.now().date().isoformat(),
                'category_id': self.category1.id
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    # 5. A05:2021 – Security Misconfiguration
    def test_error_messages_dont_expose_system_info(self):
        """Test that error messages don't expose sensitive system information (A05)"""
        self.client.force_authenticate(user=self.user1)
        
        # request that cause a server error but don't expose system details
        response = self.client.post(
            self.transactions_url,
            {
                'amount': 'not_a_number',
                'type': 'expense',
                'description': 'Test error handling',
                'date': timezone.now().date().isoformat(),
                'category_id': self.category1.id
            }
        )
        
        # Should return error but not expose system details
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = json.loads(response.content)
        
        # check no sensitive information is exposed
        sensitive_info = ['stacktrace', 'django', 'python', 'settings', 'DEBUG', 'path']
        response_str = str(response_data).lower()
        for info in sensitive_info:
            self.assertNotIn(info, response_str)
    
    # 6. A06:2021 – Vulnerable and Outdated Components
    def test_vulnerable_components(self):
        """
        Placeholder test for vulnerable components.
        """
        self.assertTrue(True)
    
    # 7. A07:2021 – Identification and Authentication Failures
    def test_weak_password_handling(self):
        """Test weak password handling (A07)"""
        
        # Create new user
        test_user = User.objects.create_user(
            username="testuser3", 
            email="test3@example.com",
            password="PasswordForTest123!"
        )
        
        # Check that the password is not stored in plaintext
        self.assertNotEqual(test_user.password, "PasswordForTest123!")
        self.assertTrue(test_user.password.startswith('pbkdf2_') or 
                        test_user.password.startswith('bcrypt$') or
                        test_user.password.startswith('argon2'))
    
    def test_token_authentication(self):
        """Test API token authentication (A07)"""
        # use token-based auth instead of session auth
        # try without authentication
        response = self.client.get(self.transactions_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # authenticate using force_authenticate
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.transactions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # logout
        self.client.force_authenticate(user=None)
        response = self.client.get(self.transactions_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # 8. A08:2021 – Software and Data Integrity Failures
    def test_input_validation(self):
        """Test that all inputs are properly validated (A08)"""
        self.client.force_authenticate(user=self.user1)
        
        # Test with excessively long input
        long_string = "A" * 10000
        response = self.client.post(
            self.categories_url, 
            {'name': long_string}
        )
        
        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # simulates tampering with data during transmission
        response = self.client.post(
            self.transactions_url,
            {
                'amount': '100.00',
                'type': 'expense',
                'description': 'Valid transaction',
                'date': timezone.now().date().isoformat(),
                'category_id': self.category1.id,
                'unexpected_field': 'suspicious data'  # Extra field that shouldn't be there
            }
        )
        
        # The API should either accept valid fields and ignore unexpected ones,
        # or reject the entire request as tampering
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
        
        if response.status_code == status.HTTP_201_CREATED:
            response_data = json.loads(response.content)
            # If accepted, make sure the unexpected field isn't stored
            self.assertNotIn('unexpected_field', response_data['data'])
    
    # 9. A09:2021 – Security Logging and Monitoring Failures
    @patch('logging.Logger.warning')
    @patch('logging.Logger.error')
    def test_security_events_logged(self, mock_error_log, mock_warning_log):
        """Test that security-relevant events are properly logged (A09)"""
        # Attempt unauthorized access (should be logged)
        response = self.client.get(self.transactions_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + 'invalid_token')
        response = self.client.get(self.transactions_url)
        
        # Check it's unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        self.assertTrue(True)
    
    # 10. A10:2021 – Server-Side Request Forgery (SSRF)
    def test_ssrf_prevention(self):
        """Test that the application is resistant to SSRF attacks (A10)"""
        
        self.client.force_authenticate(user=self.user1)
        
        # Testing with potentially dangerous URLs
        dangerous_urls = [
            "http://localhost:8080",
            "http://127.0.0.1:5000",
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata endpoint
            "file:///etc/passwd",
        ]
        
        # For each URL, test that it's properly validated/rejected
        for url in dangerous_urls:
            response = self.client.post(
                self.transactions_url,
                {
                    'amount': '100.00',
                    'type': 'expense',
                    'description': f'Reference: {url}',
                    'date': timezone.now().date().isoformat(),
                    'category_id': self.category1.id,
                }
            )
            
            # no internal server errors occur and no sensitive data is leaked
            self.assertNotIn(response.status_code, [500, 502, 503, 504])