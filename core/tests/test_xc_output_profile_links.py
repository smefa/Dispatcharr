"""Fork feature: per-output-profile Xtream Codes links (http://host:port/<xc_path>).

These run before every automated upstream-release image is published, so a
merge that silently drops part of the feature fails the release instead.
"""
from unittest.mock import patch
from uuid import uuid4

from django.conf import settings
from django.db import IntegrityError, transaction
from django.test import Client, RequestFactory, TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.channels.models import Channel, ChannelGroup
from apps.proxy.live_proxy.views import _resolve_output_profile
from core.models import OutputProfile

MIDDLEWARE = "dispatcharr.output_profile_middleware.output_profile_prefix_middleware"
PARAMETERS = "-i pipe:0 -c copy -f mpegts pipe:1"


def _profile(name, xc_path="", **kwargs):
    return OutputProfile.objects.create(
        name=name, command="ffmpeg", parameters=PARAMETERS, xc_path=xc_path, **kwargs
    )


class MiddlewareRegistrationTests(TestCase):
    def test_prefix_middleware_is_installed(self):
        self.assertIn(MIDDLEWARE, settings.MIDDLEWARE)


class ResolveOutputProfileTests(TestCase):
    def setUp(self):
        self.low = _profile("Low", "low")
        self.factory = RequestFactory()

    def _resolve(self, value):
        return _resolve_output_profile(self.factory.get("/", {"output_profile": value}), None)

    def test_xc_path_matches_case_insensitively(self):
        self.assertEqual(self._resolve("low"), self.low)
        self.assertEqual(self._resolve("LOW"), self.low)

    def test_numeric_id_still_resolves(self):
        self.assertEqual(self._resolve(str(self.low.id)), self.low)

    def test_unknown_or_inactive_profile_is_ignored(self):
        self.assertIsNone(self._resolve("missing"))
        self.low.is_active = False
        self.low.save()
        self.assertIsNone(self._resolve("low"))


class XcPlaylistThroughProfileLinkTests(TestCase):
    def setUp(self):
        for target in ("apps.output.views.network_access_allowed",
                       "apps.accounts.xc_auth.network_access_allowed"):
            patcher = patch(target, return_value=True)
            patcher.start()
            self.addCleanup(patcher.stop)
        for target in ("apps.output.views.log_system_event",
                       "django.db.close_old_connections"):
            patcher = patch(target)
            patcher.start()
            self.addCleanup(patcher.stop)
        _profile("Low", "low")
        User.objects.create_user(
            username="xcuser", password="pass", user_level=10,
            custom_properties={"xc_password": "xcpass"},
        )
        group = ChannelGroup.objects.create(name=f"XC {uuid4().hex[:8]}")
        self.channel = Channel.objects.create(
            channel_group=group, channel_number=1.0, name="XC Channel"
        )

    def tearDown(self):
        from django.core.cache import cache

        cache.clear()

    def test_profile_link_playlist_streams_use_the_profile(self):
        response = Client().get("/low/get.php", {"username": "xcuser", "password": "xcpass"})
        self.assertEqual(response.status_code, 200)
        content = (b"".join(response.streaming_content) if response.streaming
                   else response.content).decode()
        self.assertIn(f"/live/xcuser/xcpass/{self.channel.id}?output_profile=low", content)


class XcPathApiTests(TestCase):
    def setUp(self):
        admin = User.objects.create_user(username="xc-admin", password="x", user_level=10)
        self.client = APIClient()
        self.client.force_authenticate(admin)
        self.profile = _profile("Custom")

    def _patch(self, xc_path):
        return self.client.patch(
            f"/api/core/outputprofiles/{self.profile.id}/", {"xc_path": xc_path}, format="json"
        )

    def test_xc_path_is_saved_and_returned(self):
        response = self._patch("tv-low")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["xc_path"], "tv-low")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.xc_path, "tv-low")

    def test_xc_path_rejects_url_characters(self):
        self.assertEqual(self._patch("low/high").status_code, 400)


class XcPathUniquenessTests(TestCase):
    def test_paths_are_unique_but_empty_is_shared(self):
        _profile("A", "low")
        _profile("B")
        _profile("C")
        with self.assertRaises(IntegrityError), transaction.atomic():
            _profile("D", "low")
