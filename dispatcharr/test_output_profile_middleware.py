from django.test import RequestFactory, SimpleTestCase

from dispatcharr.output_profile_middleware import output_profile_prefix_middleware


class OutputProfilePrefixMiddlewareTests(SimpleTestCase):
    def _run(self, path):
        seen = {}

        def view(request):
            seen['path'] = request.path_info
            seen['profile'] = request.GET.get('output_profile')
            seen['user'] = request.GET.get('username')
            return None

        output_profile_prefix_middleware(view)(RequestFactory().get(path))
        return seen

    def test_numeric_prefix_is_stripped(self):
        seen = self._run('/2525/player_api.php?username=u')
        self.assertEqual(seen['path'], '/player_api.php')
        self.assertEqual(seen['profile'], '2525')
        self.assertEqual(seen['user'], 'u')

    def test_name_prefix_is_stripped(self):
        seen = self._run('/low/live/u/p/1.ts')
        self.assertEqual(seen['path'], '/live/u/p/1.ts')
        self.assertEqual(seen['profile'], 'low')

    def test_non_xc_paths_untouched(self):
        seen = self._run('/api/channels/')
        self.assertEqual(seen['path'], '/api/channels/')
        self.assertIsNone(seen['profile'])

    def test_other_paths_untouched(self):
        seen = self._run('/player_api.php')
        self.assertEqual(seen['path'], '/player_api.php')
        self.assertIsNone(seen['profile'])

    def test_complete_xc_routes(self):
        for path in (
            '/player_api.php',
            '/panel_api.php',
            '/get.php',
            '/xmltv.php',
            '/live/u/p/1.ts',
            '/live/u/p/1.m3u8',
            '/movie/u/p/1.mp4',
            '/series/u/p/1.mkv',
        ):
            with self.subTest(path=path):
                seen = self._run(f'/low{path}')
                self.assertEqual(seen['path'], path)
                self.assertEqual(seen['profile'], 'low')

    def test_legacy_credentials_and_incomplete_routes_are_untouched(self):
        for path in (
            '/john/live/1.ts',
            '/john/movie/1.ts',
            '/john/series/1.ts',
            '/live/u/p/1.ts',
            '/movie/u/p/1.mp4',
            '/series/u/p/1.mkv',
            '/low/live/u/p/1.ts/extra',
            '/low/movie/u/p/1',
            '/low/player_api.php/extra',
            '/low/player_api.php.bak',
            '/low/live//p/1.ts',
        ):
            with self.subTest(path=path):
                seen = self._run(path)
                self.assertEqual(seen['path'], path)
                self.assertIsNone(seen['profile'])

    def test_prefix_overrides_query_profile_without_losing_other_parameters(self):
        seen = self._run('/low/player_api.php?output_profile=other&username=u')
        self.assertEqual(seen['profile'], 'low')
        self.assertEqual(seen['user'], 'u')

    def test_script_prefix_is_preserved(self):
        request = RequestFactory().get(
            '/low/live/u/p/1.ts', SCRIPT_NAME='/dispatcharr'
        )
        output_profile_prefix_middleware(lambda request: None)(request)
        self.assertEqual(request.path_info, '/live/u/p/1.ts')
        self.assertEqual(request.path, '/dispatcharr/live/u/p/1.ts')
