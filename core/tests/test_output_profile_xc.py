from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import resolve
from rest_framework.test import APIClient

from apps.proxy.live_proxy.views import _resolve_output_profile
from core.models import OutputProfile
from core.serializers import OutputProfileSerializer
from dispatcharr.output_profile_middleware import output_profile_prefix_middleware


class OutputProfileXCTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.profile = OutputProfile.objects.create(
            name="Lowercase alias",
            command="ffmpeg",
            parameters="-i pipe:0 -c copy -f mpegts pipe:1",
            xc_path="low",
        )
        cls.uppercase = OutputProfile.objects.create(
            name="Uppercase alias",
            command="ffmpeg",
            parameters=cls.profile.parameters,
            xc_path="LOW",
        )
        cls.inactive = OutputProfile.objects.create(
            name="Inactive alias",
            command="ffmpeg",
            parameters=cls.profile.parameters,
            xc_path="inactive",
            is_active=False,
        )

    def _resolve(self, value=None, user=None):
        params = {} if value is None else {"output_profile": value}
        request = RequestFactory().get("/live/u/p/1.ts", params)
        return _resolve_output_profile(request, user)

    def test_aliases_are_case_sensitive(self):
        self.assertEqual(self._resolve("low"), self.profile)
        self.assertEqual(self._resolve("LOW"), self.uppercase)
        self.assertIsNone(self._resolve("Low"))

    def test_numeric_ids_still_work(self):
        self.assertEqual(self._resolve(str(self.profile.id)), self.profile)
        self.assertEqual(self._resolve(f"000{self.profile.id}"), self.profile)

    def test_unknown_and_inactive_profiles_are_not_selected(self):
        for value in ("unknown", "inactive", str(self.inactive.id), "0"):
            with self.subTest(value=value):
                self.assertIsNone(self._resolve(value))

    def test_out_of_range_ids_do_not_raise(self):
        for value in ("9" * 4301, "9223372036854775808", "\u0669" * 4301):
            with self.subTest(length=len(value)):
                with self.assertLogs("live_proxy.views", level="WARNING"):
                    self.assertIsNone(self._resolve(value))
        self.assertIsNone(self._resolve("9223372036854775807"))
        self.assertEqual(
            self._resolve("0" * 4301 + str(self.profile.id)), self.profile
        )

    def test_query_profile_takes_precedence_over_user_default(self):
        user = SimpleNamespace(
            custom_properties={"output_profile": self.uppercase.id}
        )
        self.assertEqual(self._resolve(user=user), self.uppercase)
        self.assertEqual(self._resolve("low", user), self.profile)
        self.assertIsNone(self._resolve("unknown", user))
        self.assertIsNone(self._resolve("inactive", user))

    def test_serializer_accepts_empty_and_valid_aliases(self):
        for alias in ("", "low_720-p", "a" * 64):
            with self.subTest(alias=alias):
                serializer = OutputProfileSerializer(
                    self.uppercase, data={"xc_path": alias}, partial=True
                )
                self.assertTrue(serializer.is_valid(), serializer.errors)
                self.assertEqual(serializer.validated_data["xc_path"], alias)

    def test_model_and_serializer_reject_invalid_aliases(self):
        for alias in (
            "2525", "0", "a" * 65, "bad/path", "bad alias", "bad\npath", "\u0661"
        ):
            with self.subTest(alias=alias):
                profile = OutputProfile(
                    name="Invalid alias",
                    command="ffmpeg",
                    parameters=self.profile.parameters,
                    xc_path=alias,
                )
                with self.assertRaises(ValidationError) as error:
                    profile.full_clean()
                self.assertIn("xc_path", error.exception.message_dict)
                serializer = OutputProfileSerializer(
                    self.uppercase, data={"xc_path": alias}, partial=True
                )
                self.assertFalse(serializer.is_valid())
                self.assertIn("xc_path", serializer.errors)

    def test_duplicate_alias_is_rejected_by_serializer_and_database(self):
        serializer = OutputProfileSerializer(
            self.uppercase, data={"xc_path": "low"}, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("xc_path", serializer.errors)
        with self.assertRaises(IntegrityError), transaction.atomic():
            OutputProfile.objects.create(
                name="Duplicate alias",
                command="ffmpeg",
                parameters=self.profile.parameters,
                xc_path="low",
            )

    def test_multiple_profiles_can_disable_the_alias(self):
        for name in ("No alias one", "No alias two"):
            OutputProfile.objects.create(
                name=name, command="ffmpeg", parameters=self.profile.parameters
            )
        self.assertEqual(
            OutputProfile.objects.filter(
                name__startswith="No alias", xc_path=""
            ).count(),
            2,
        )

    def test_prefixed_route_reaches_the_existing_view_with_selected_profile(self):
        request = RequestFactory().get("/low/live/u/p/1.ts?output_profile=other")

        def view(request):
            match = resolve(request.path_info)
            self.assertEqual(match.url_name, "xc_live_stream_endpoint")
            self.assertEqual(
                match.kwargs,
                {"username": "u", "password": "p", "channel_id": "1.ts"},
            )
            self.assertEqual(_resolve_output_profile(request, None), self.profile)
            return HttpResponse()

        response = output_profile_prefix_middleware(view)(request)
        self.assertEqual(response.status_code, 200)

    def test_prefixed_live_route_preserves_auth_rejection(self):
        with patch("apps.proxy.live_proxy.views.close_old_connections"), patch(
            "apps.proxy.live_proxy.views.authorize_xc_client",
            return_value=(None, HttpResponse(status=401)),
        ) as authorize, patch("apps.proxy.live_proxy.views.stream_ts") as stream:
            response = self.client.get("/low/live/u/p/1.ts")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(authorize.call_args.args[1:3], ("u", "p"))
        stream.assert_not_called()

    def test_prefixed_api_route_preserves_auth_rejection(self):
        with patch(
            "apps.output.views.authorize_xc_client",
            return_value=(None, HttpResponse(status=403)),
        ):
            response = self.client.get("/low/player_api.php?username=u&password=p")
        self.assertEqual(response.status_code, 403)


class OutputProfileXCApiTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="xc-profile-admin", user_level=10
        )
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        self.profile = OutputProfile.objects.create(
            name="API profile",
            command="ffmpeg",
            parameters="-i pipe:0 -c copy -f mpegts pipe:1",
            xc_path="low",
        )
        self.url = f"/api/core/outputprofiles/{self.profile.id}/"

    def test_admin_can_create_update_and_clear_alias(self):
        response = self.client.post(
            "/api/core/outputprofiles/",
            {
                "name": "Created via API",
                "command": "ffmpeg",
                "parameters": self.profile.parameters,
                "xc_path": "LOW",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["xc_path"], "LOW")
        for alias in ("low_720", ""):
            response = self.client.patch(
                self.url, {"xc_path": alias}, format="json"
            )
            self.assertEqual(response.status_code, 200)
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.xc_path, alias)

    def test_numeric_and_duplicate_aliases_return_validation_errors(self):
        for alias in ("2525", "a" * 65, "bad/path"):
            with self.subTest(alias=alias):
                response = self.client.patch(
                    self.url, {"xc_path": alias}, format="json"
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn("xc_path", response.data)
        response = self.client.post(
            "/api/core/outputprofiles/",
            {
                "name": "Duplicate via API",
                "command": "ffmpeg",
                "parameters": self.profile.parameters,
                "xc_path": "low",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("xc_path", response.data)

    def test_locked_profile_alias_cannot_be_changed(self):
        locked = OutputProfile.objects.get(name="Web Player (AAC Audio)")
        response = self.client.patch(
            f"/api/core/outputprofiles/{locked.id}/",
            {"xc_path": "locked"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        locked.refresh_from_db()
        self.assertEqual(locked.xc_path, "")

    def test_non_admin_cannot_change_alias(self):
        user = get_user_model().objects.create_user(
            username="xc-profile-viewer", user_level=0
        )
        self.client.force_authenticate(user)
        response = self.client.patch(
            self.url, {"xc_path": "changed"}, format="json"
        )
        self.assertEqual(response.status_code, 403)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.xc_path, "low")
