def response_error(response, service):
    return "%s Error Code: %s" % (service, response.status_code)
