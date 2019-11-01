import os


def export_environ(request):
    return {"environ": os.environ}
