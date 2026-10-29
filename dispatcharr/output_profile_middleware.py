import re

# Lets Xtream Codes apps, which only accept a base URL, select an output
# profile: http://host:port/output_profile/<id-or-name> is the server URL.
_PREFIX_RE = re.compile(r'^/output_profile/([^/]+)(/.*)$')


class OutputProfilePrefixMiddleware:
    """Strip an /output_profile/<id-or-name> path prefix and expose it as the
    ?output_profile= query parameter."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        match = _PREFIX_RE.match(request.path_info)
        if match:
            profile, rest = match.groups()
            request.path_info = rest
            request.path = rest
            get = request.GET.copy()
            get['output_profile'] = profile
            request.GET = get
        return self.get_response(request)
