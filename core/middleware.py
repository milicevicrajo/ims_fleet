from core.activity import log_request_activity


class ActivityLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        log_request_activity(request, response)
        return response
