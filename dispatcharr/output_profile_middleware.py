import re

# Xtream Codes apps only take a base URL, so /output_profile/<id-or-name>/...
# is rewritten to /... with ?output_profile=<id-or-name>.
_PREFIX_RE = re.compile(r'^/output_profile/([^/]+)(/.*)$')


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
