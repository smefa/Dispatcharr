from django.test import RequestFactory, SimpleTestCase

from dispatcharr.output_profile_middleware import OutputProfilePrefixMiddleware


class OutputProfilePrefixMiddlewareTests(SimpleTestCase):
    def _run(self, path):
        seen = {}

        def view(request):
            seen['path'] = request.path_info
            seen['profile'] = request.GET.get('output_profile')
            seen['user'] = request.GET.get('username')
            return None

        OutputProfilePrefixMiddleware(view)(RequestFactory().get(path))
        return seen

    def test_numeric_prefix_is_stripped(self):
        seen = self._run('/output_profile/2525/player_api.php?username=u')
        self.assertEqual(seen['path'], '/player_api.php')
        self.assertEqual(seen['profile'], '2525')
        self.assertEqual(seen['user'], 'u')

    def test_name_prefix_is_stripped(self):
        seen = self._run('/output_profile/low/live/u/p/1.ts')
        self.assertEqual(seen['path'], '/live/u/p/1.ts')
        self.assertEqual(seen['profile'], 'low')

    def test_other_paths_untouched(self):
        seen = self._run('/player_api.php')
        self.assertEqual(seen['path'], '/player_api.php')
        self.assertIsNone(seen['profile'])
