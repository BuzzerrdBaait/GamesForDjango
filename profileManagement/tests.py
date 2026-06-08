import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import FriendRequest, Message, UserOptions


class ProfileManagementApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.alice = User.objects.create_user(username="alice", email="alice@example.com", password="pw12345")
        self.bob = User.objects.create_user(username="bob", email="bob@example.com", password="pw12345")
        self.charlie = User.objects.create_user(username="charlie", email="charlie@example.com", password="pw12345")

        FriendRequest.objects.create(sender=self.alice, receiver=self.bob, status="accepted")

    def test_login_and_register_pages_load(self):
        self.assertEqual(self.client.get(reverse("profileManagement:loginUser")).status_code, 200)
        self.assertEqual(self.client.get(reverse("profileManagement:register")).status_code, 200)

    def test_save_options_valid_language(self):
        self.client.login(username="alice", password="pw12345")
        response = self.client.post(
            reverse("profileManagement:save_options"),
            data=json.dumps({"language": "fr", "time_format": "12h"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        opts = UserOptions.objects.get(user=self.alice)
        self.assertEqual(opts.language, "fr")
        self.assertEqual(opts.time_format, "12h")

    def test_save_options_invalid_language_rejected(self):
        self.client.login(username="alice", password="pw12345")
        response = self.client.post(
            reverse("profileManagement:save_options"),
            data=json.dumps({"language": "xx"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_send_message_requires_friendship(self):
        self.client.login(username="alice", password="pw12345")
        response = self.client.post(
            reverse("profileManagement:send_message"),
            data=json.dumps({"receiver_id": self.charlie.pk, "content": "hello"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_send_and_fetch_conversation_for_friends(self):
        self.client.login(username="alice", password="pw12345")
        send_response = self.client.post(
            reverse("profileManagement:send_message"),
            data=json.dumps({"receiver_id": self.bob.pk, "content": "hey bob"}),
            content_type="application/json",
        )
        self.assertEqual(send_response.status_code, 200)
        self.assertEqual(Message.objects.count(), 1)

        self.client.logout()
        self.client.login(username="bob", password="pw12345")
        convo_response = self.client.get(reverse("profileManagement:get_conversation", args=[self.alice.pk]))
        self.assertEqual(convo_response.status_code, 200)
        payload = convo_response.json()
        self.assertTrue(payload["messages"])
        self.assertEqual(payload["messages"][0]["content"], "hey bob")
