import os
import django

# Django設定を読み込み
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shift_table.settings")
django.setup()

from django.test import Client, TestCase
from django.contrib.auth.models import User
from django.urls import reverse


class DirectPasswordChangeTest(TestCase):
    def setUp(self):
        """テスト用のユーザーを作成"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="oldpassword123", email="test@example.com"
        )
        self.admin_user = User.objects.create_superuser(
            username="admin", password="adminpass123", email="admin@example.com"
        )

    def test_direct_password_change_page_access(self):
        """直接パスワード変更ページにアクセスできることを確認"""
        response = self.client.get(reverse("direct_password_change"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "直接パスワード変更")
        self.assertContains(response, "ユーザー名")
        self.assertContains(response, "新しいパスワード")

    def test_direct_password_change_success(self):
        """正常なパスワード変更が成功することを確認"""
        data = {
            "username": "testuser",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }
        response = self.client.post(reverse("direct_password_change"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "パスワードが正常に変更されました")

        # 新しいパスワードでログインできることを確認
        login_success = self.client.login(
            username="testuser", password="newpassword123"
        )
        self.assertTrue(login_success)

    def test_direct_password_change_admin_user(self):
        """管理者ユーザーのパスワード変更が成功することを確認"""
        data = {
            "username": "admin",
            "new_password": "newadminpass123",
            "confirm_password": "newadminpass123",
        }
        response = self.client.post(reverse("direct_password_change"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "パスワードが正常に変更されました")

        # 新しいパスワードでログインできることを確認
        login_success = self.client.login(username="admin", password="newadminpass123")
        self.assertTrue(login_success)

    def test_direct_password_change_missing_fields(self):
        """必須フィールドが不足している場合のエラー処理"""
        data = {
            "username": "testuser",
            "new_password": "newpassword123",
            # confirm_password が不足
        }
        response = self.client.post(reverse("direct_password_change"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "すべての項目を入力してください")

    def test_direct_password_change_password_mismatch(self):
        """パスワードが一致しない場合のエラー処理"""
        data = {
            "username": "testuser",
            "new_password": "newpassword123",
            "confirm_password": "differentpassword123",
        }
        response = self.client.post(reverse("direct_password_change"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "パスワードが一致しません")

    def test_direct_password_change_short_password(self):
        """パスワードが短すぎる場合のエラー処理"""
        data = {
            "username": "testuser",
            "new_password": "short",
            "confirm_password": "short",
        }
        response = self.client.post(reverse("direct_password_change"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "パスワードは8文字以上で入力してください")

    def test_direct_password_change_nonexistent_user(self):
        """存在しないユーザー名の場合のエラー処理"""
        data = {
            "username": "nonexistentuser",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }
        response = self.client.post(reverse("direct_password_change"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "指定されたユーザー名が見つかりません")

    def test_direct_password_change_empty_fields(self):
        """空のフィールドが送信された場合のエラー処理"""
        data = {"username": "", "new_password": "", "confirm_password": ""}
        response = self.client.post(reverse("direct_password_change"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "すべての項目を入力してください")

    def test_direct_password_change_get_request(self):
        """GETリクエストでページが正しく表示されることを確認"""
        response = self.client.get(reverse("direct_password_change"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")
        self.assertContains(response, 'method="post"')

    def test_direct_password_change_csrf_protection(self):
        """CSRF保護が有効であることを確認（フォームにCSRFトークンが含まれていること）"""
        response = self.client.get(reverse("direct_password_change"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_direct_password_change_success_page_content(self):
        """成功ページの内容が正しいことを確認"""
        data = {
            "username": "testuser",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }
        response = self.client.post(reverse("direct_password_change"), data)
        self.assertContains(response, "パスワードが正常に変更されました")
        self.assertContains(response, "testuser")
        self.assertContains(response, "管理画面にログイン")
