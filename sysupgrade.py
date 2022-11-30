#!/usr/bin/env python3
import requests
import json
import flask
from flask_cors import CORS
import hashlib
import os
import shutil

app = flask.Flask(__name__, template_folder="template")
CORS(app)

config = json.load(open('config.json'))
cache = {"link": None, "jdata": {"update": None, "sha": None, "sums": None}}


class Updater(object):
    baseurl = "https://api.github.com/repos/robimarko/openwrt"
    session = requests.Session()
    session.headers = {"Authorization": f"Bearer {config['key']}"}
    jdata = None

    def __init__(self) -> None:
        if not os.path.isdir("cache"):
            os.mkdir("cache")

    def clear_old_cache(self):
        basedir = f'cache/{self.jdata["id"]}'
        if os.path.isdir(basedir):
            shutil.rmtree(basedir)

    def get_update(self) -> dict:
        latestrel = f"{self.baseurl}/releases"
        r = self.session.head(latestrel, params={"per_page": "1"})
        linksha = hashlib.sha256(r.headers['link'].encode()).hexdigest()
        if linksha != cache['link']:
            print("New data!", linksha, cache['link'])
            if cache['link']:
                self.clear_old_cache()

            cache['link'] = linksha

            r = self.session.get(latestrel, params={"per_page": "1"})
            self.jdata = r.json()[0]
            cache["jdata"]["update"] = self.jdata
            cache["jdata"]["sha"] = None
            cache["jdata"]["sums"] = None
        else:
            self.jdata = cache["jdata"]["update"]
        return self.jdata

    def get_sha(self) -> dict:
        if cache["jdata"]["sha"]:
            return cache["jdata"]["sha"]
        tagname = self.jdata['tag_name']
        get_tag = f"{self.baseurl}/git/ref/tags/{tagname}"
        r = self.session.get(get_tag)
        jdata = r.json()
        sha = jdata['object']['sha']
        ssha = sha[:7]
        cache["jdata"]["sha"] = ssha
        return ssha

    def get_models(self, nosha=False) -> dict:
        models = {}
        for asset in self.jdata['assets']:
            name = asset["name"]
            if "sysupgrade" in name or (name == "sha256sums" and nosha == False):
                if name != "sha256sums":
                    model = name.split("-")[3]
                else:
                    model = name
                if not model in models:
                    models[model] = asset
        return models

    def get_sums(self) -> dict:
        models = self.get_models()
        if cache["jdata"]["sums"]:
            return cache["jdata"]["sums"]
        sums = models["sha256sums"]["browser_download_url"]
        r = self.session.get(sums)
        sumsdict = {}
        for line in r.text.split('\n'):
            line = line.strip()
            if not line:
                continue
            sha, fname = line.split()[0:2]
            fname = fname.replace("*", "")
            sumsdict[fname] = sha
        cache["jdata"]["sums"] = sumsdict
        return sumsdict

    def get_file(self, url: str) -> requests.Response:
        return self.session.get(url)


@app.route("/<string:model>")
@app.route("/<string:model>/api/v1/revision/SNAPSHOT/ipq807x/generic")
def get_model(model: str):
    model = model.replace("/", "")
    u = Updater()
    u.get_update()
    models = u.get_models(nosha=True)
    if not model in models:
        return {
            "detail": f"Allowed models: {','.join(models)}",
            "status": 500,
            "title": "Internal Server Error",
            "type": "about:blank"
        }, 500
    ssha = u.get_sha()
    return {"revision": f"r0-{ssha}"}


@app.route("/<string:model>/store/undefined/<path:fname>.bin")
def store(model: str, fname: str):
    model = model.replace("/", "")
    u = Updater()
    update = u.get_update()
    models = u.get_models(nosha=True)
    if not model in models:
        return {
            "detail": f"Allowed models: {','.join(models)}",
            "status": 500,
            "title": "Internal Server Error",
            "type": "about:blank"
        }, 500
    basedir = f'cache/{update["id"]}'
    if not os.path.isdir(basedir):
        os.mkdir(basedir)
    download_url = models[model]['browser_download_url']
    bname = os.path.basename(download_url)
    if not os.path.exists(f"{basedir}/{bname}"):
        r = u.get_file(download_url)
        with open(f"{basedir}/{bname}", "wb") as f:
            f.write(r.content)
    return flask.send_from_directory(basedir, bname)


@app.route("/<string:model>/api/v1/build", methods=["GET", "POST"])
def build(model: str):
    model = model.replace("/", "")
    u = Updater()
    u.get_update()
    models = u.get_models(nosha=True)
    if not model in models:
        return {
            "detail": f"Allowed models: {','.join(models)}",
            "status": 500,
            "title": "Internal Server Error",
            "type": "about:blank"
        }, 500
    model_data = models[model]
    sums = u.get_sums()
    checksum = None
    for file in sums:
        if file == model_data["name"]:
            checksum = sums[file]
    build_data = {
        "build_at": model_data['created_at'],
        "build_cmd": [
            "string"
        ],
        "enqueued_at": model_data['created_at'],
        "id": model_data['id'],
        "image_prefix": model_data["name"].split('.')[0],
        "imagebuilder_status": "download_imagebuilder",
        "images": [
            {
                "name": model_data["name"],
                "sha256": checksum,
                "type": "eva"
            }
        ],
        "manifest": {
            "additionalProp1": "string",
            "additionalProp2": "string",
            "additionalProp3": "string"
        },
        "metadata_version": 1,
        "request_hash": checksum[0:12],
        "status": 200,
        "supported_devices": [
            model
        ],
        "target": "ipq807x/generic",
        "titles": [
            {
                "model": model.split("_")[1],
                "variant": "GENERIC",
                "vendor": model.split("_")[0]
            },
            {
                "title": model
            }
        ],
        "version_code": f"r0-{u.get_sha()}",
        "version_number": "SNAPSHOT"
    }
    return build_data


@app.route("/")
def index():
    u = Updater()
    u.get_update()
    models = u.get_models(nosha=True)
    host = flask.request.host
    proto = flask.request.url.startswith('http://') and "http" or "https"
    return flask.render_template("index.html", host=host, models=models, proto=proto)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
