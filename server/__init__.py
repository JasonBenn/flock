import os
import sys

from flask import request, send_file
from flask import Flask, Response


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'server.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/', methods=['GET', 'POST'])
    def root():
        return send_file('index.html')


    @app.route('/echo', methods=['GET', 'POST'])
    def log():
        print('\n')
        print('\n====')
        print(request.headers, file=sys.stderr)
        print(request.data, file=sys.stderr)
        print('=====\n')
        print('\n')
        return "test"

    @app.route('/echo-ip')
    def echo():
        ip = None
        print(request.headers)
        if not request.headers.getlist("X-Forwarded-For"):
            ip = request.remote_addr
        else:
            ip = request.headers.getlist("X-Forwarded-For")[0]
        return ip

    return app