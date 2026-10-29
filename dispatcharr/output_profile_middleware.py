import re

# Xtream Codes apps only take a base URL, so /<profile>/player_api.php (or any
# other XC path) is rewritten to /player_api.php with ?output_profile=<profile>.
_PREFIX_RE = re.compile(
    r'^/([A-Za-z0-9_-]+)(/(?:player_api\.php|get\.php|xmltv\.php|live/|movie/|series/).*)$'
)


def output_profile_prefix_middleware(get_response):
    def middleware(request):
        match = _PREFIX_RE.match(request.path_info)
        if match:
            profile, request.path_info = match.groups()
            request.path = request.path_info
            request.GET = request.GET.copy()
            request.GET['output_profile'] = profile
        return get_response(request)

    return middleware
