from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


def testview(request):
    output = """
    current user: {}
    is_authenticated: {}
    is_staff: {}
    is_superuser: {}
    """.format(
        request.user,
        request.user.is_authenticated,
        request.user.is_staff,
        request.user.is_superuser,
    )
    return HttpResponse(output)


@login_required
def protected(request):
    output = """
    current user: {}
    is_authenticated: {}
    is_staff: {}
    is_superuser: {}
    """.format(
        request.user,
        request.user.is_authenticated,
        request.user.is_staff,
        request.user.is_superuser,
    )
    return HttpResponse(output)
