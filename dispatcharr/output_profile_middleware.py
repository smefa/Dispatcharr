import re

# Match complete XC routes so legacy /username/password/channel URLs are
# untouched even when a password is "live", "movie", or "series".
_PREFIX_RE = re.compile(
    r'\A/([A-Za-z0-9_-]+)(/(?:'
    r'(?:player_api|panel_api|get|xmltv)\.php'
    r'|live/[^/]+/[^/]+/[^/]+'
    r'|(?:movie|series)/[^/]+/[^/]+/[^/]+\.[^/.]+'
    r'))\Z'
)


def output_profile_prefix_middleware(get_response):
    def middleware(request):
        match = _PREFIX_RE.match(request.path_info)
        if match:
            profile, path_info = match.groups()
            script_prefix = request.path[:-len(request.path_info)]
            request.path_info = path_info
            request.path = script_prefix + path_info
            request.GET = request.GET.copy()
            request.GET['output_profile'] = profile
        return get_response(request)

    return middleware
