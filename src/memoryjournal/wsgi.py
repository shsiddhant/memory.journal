from gunicorn.app.wsgiapp import WSGIApplication

class StandaloneWSGIApplication(WSGIApplication):

    def __init__(self, app_uri, options=None):
        self.options = options or {}
        self.app_uri = app_uri
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

def run_with_gunicorn():
    options = {
        "bind": "0.0.0.0:5000",
        "workers": 3,
        "wsgi_app": "memoryjournal:create_app()"
    }
    StandaloneWSGIApplication(options.get("wsgi_app"), options).run()


if __name__ == "__main__":
    run_with_gunicorn()
