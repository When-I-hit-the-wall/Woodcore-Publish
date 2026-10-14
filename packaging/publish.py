"""Publishes a built installer, so that the website offers it and every installed Woodcore announces it (docs/conventions/build-and-release.md §12, v0.89; on GitHub since v0.117).

    python packaging/publish.py                    the installer of calc/project.py's VERSION, from dist/
    python packaging/publish.py --version 0.117.0  another one dist/ holds
    python packaging/publish.py --dry-run          says what it would send, sends nothing
    python packaging/publish.py --replace          deletes the asset of that name the Release already has, then uploads this one

What it does, in order, and it stops at the first thing that is not right:

1. **The installer** is `dist/Woodcore-<version>-setup.exe`, which packaging/build.py wrote -- by hand, or by itself at the commit that changed VERSION (packaging/auto_build.py). Its size and its SHA-256 are computed here.
2. **Its notes** are the entry of `website/releases.json` for that version, in French, German and English, written by hand before publishing: what Woodcore's window shows under «Woodcore 0.117.0 est disponible», and what the download page lists. A version with no entry, or an entry missing a language, is refused by name -- an update announced with nothing to say about it is one nobody installs.
3. **The upload**: the installer is sent as an asset of the Release `v<version>` of the public repository `releases_repo` of website/site.json (created where it is not there yet), with the engineer's token -- `WOODCORE_GITHUB_TOKEN`, else asked for. Use a fine-grained personal access token limited to that repository, with the permission *Contents: Read and write*; it is never written anywhere, and it is sent to api.github.com and uploads.github.com only, in a header urllib does not replay on a redirect. An asset of the same name that is already there is never replaced unless `--replace` says so. The address the asset will have is checked first against the rule the installed program applies (calc/tools/updates.py), so an installer the program would refuse is never uploaded.
4. **The release is written down**: the entry gets the installer's file name, size and SHA-256, where it is kept (`hosted`: "github") and its public address (`url`) -- written here and nowhere else, website/build.py reads it as it is --, and its date where it had none. That file is versioned: committing and pushing it is what makes the site's workflow (.github/workflows/site.yml) rebuild the site, download the installer from that address without any token, check it against this SHA-256, and publish `version.json` -- which is what every installed Woodcore reads at its start. The Release does not copy the notes: they live in releases.json, and a second copy would age.

Nothing is committed or pushed here: that is the engineer's step, and the script prints the two lines it takes. Standard library only.
"""

import argparse
import datetime
import getpass
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DIST = ROOT / "dist"
RELEASES = ROOT / "website" / "releases.json"
SITE = ROOT / "website" / "site.json"

API = "https://api.github.com"
# The only hosts the token is ever sent to. The upload address comes from GitHub's own answer and is checked against this before anything is sent to it.
API_HOSTS = ("api.github.com", "uploads.github.com")
API_VERSION = "2022-11-28"
LANGUAGES = ("fr", "de", "en")
TOKEN_ENV = "WOODCORE_GITHUB_TOKEN"   # never GITHUB_TOKEN: in many shells that one is a token for everything


class PublishError(Exception):
    pass


class Refused(PublishError):
    """GitHub answered with an error status; `code` is that status."""

    def __init__(self, message, code):
        super().__init__(message)
        self.code = code


def site_settings(path=None):
    return json.loads(Path(path or SITE).read_text(encoding="utf-8"))


def repository(settings=None):
    """`owner/name` of the public repository whose Releases carry the installers -- website/site.json's `releases_repo`, the one place it is written."""
    return (settings or site_settings())["releases_repo"]


def current_version():
    sys.path.insert(0, str(ROOT / "calc"))
    import project
    return project.VERSION


def installer_name(version):
    return f"Woodcore-{version}-setup.exe"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_releases(path=None):
    path = path or RELEASES
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PublishError(f"{path}: cannot be read ({exc})") from exc
    if not isinstance(data.get("releases"), list):
        raise PublishError(f"{path}: no 'releases' list")
    return data


def entry_for(data, version, path=None):
    """The release entry of `version`, checked: its notes in every language."""
    path = path or RELEASES
    entry = next((r for r in data["releases"] if r.get("version") == version), None)
    if entry is None:
        raise PublishError(f"{path} has no entry for {version}: write its notes in French, German and English first (what the update window and the download page show)")
    notes = entry.get("notes") or {}
    missing = [lang for lang in LANGUAGES if not isinstance(notes.get(lang), str) or not notes[lang].strip()]
    if missing:
        raise PublishError(f"{path}, {version}: no notes in {', '.join(missing)}")
    return entry


def tag(version):
    return f"v{version}"


def asset_url(version, name, repo=None):
    """The public address of the installer once uploaded: the one place the formula is written. website/build.py and every installed Woodcore read the address from releases.json, never recompute it."""
    return f"https://github.com/{repo or repository()}/releases/download/{tag(version)}/{urllib.parse.quote(name)}"


def address_problem(url):
    """Why the installed program would refuse `url` for an installer, "" where it would accept it (calc/tools/updates.py, the rule it applies to a manifest)."""
    sys.path.insert(0, str(ROOT / "calc" / "tools"))
    import updates
    return updates.installer_address_problem(url, updates.FEED_URL)


def token():
    if os.environ.get(TOKEN_ENV):
        return os.environ[TOKEN_ENV]
    if sys.stdin and sys.stdin.isatty():
        return getpass.getpass("GitHub token for the Releases repository (fine-grained, Contents: read and write): ").strip()
    raise PublishError(f"no token: set {TOKEN_ENV} to a fine-grained personal access token limited to {repository()}, permission Contents: Read and write")


def call(method, url, secret, payload=None, body=None, size=None, opener=urllib.request.urlopen):
    """One GitHub API request, its JSON answer ({} where there is none). `payload` is sent as JSON, `body` (a file object of `size` bytes) as the installer's own bytes. Raises Refused on an error status."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.netloc not in API_HOSTS:
        raise PublishError(f"not sending the token to {parts.netloc or url!r}: only {' and '.join(API_HOSTS)}")
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": API_VERSION, "User-Agent": "Woodcore-publish"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif body is not None:
        data = body
        headers.update({"Content-Type": "application/octet-stream", "Content-Length": str(size)})
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    # unredirected: urllib replays the ordinary headers on a redirect, to wherever it leads
    request.add_unredirected_header("Authorization", f"Bearer {secret}")
    try:
        with opener(request, timeout=600) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise Refused(f"GitHub answered {exc.code} to {method} {parts.path}: {detail}", exc.code) from exc
    except (urllib.error.URLError, OSError) as exc:
        raise PublishError(f"GitHub could not be reached: {exc}") from exc
    return json.loads(text) if text.strip() else {}


def release_of(version, secret, repo=None, base_url=None, opener=urllib.request.urlopen):
    """The Release `v<version>` of the repository, created where it is not there yet. It points to the page of what the version changes and carries no notes of its own."""
    repo = repo or repository()
    try:
        return call("GET", f"{API}/repos/{repo}/releases/tags/{tag(version)}", secret, opener=opener)
    except Refused as exc:
        if exc.code != 404:
            raise PublishError(str(exc)) from exc
    page = (base_url or site_settings()["base_url"]) + f"fr/changes/{version}/"
    try:
        return call("POST", f"{API}/repos/{repo}/releases", secret, opener=opener, payload={
            "tag_name": tag(version), "name": f"Woodcore {version}", "draft": False, "prerelease": False,
            "body": f"The installer of Woodcore {version}. What it changes: {page}"})
    except Refused as exc:
        raise PublishError(f"{exc} (an empty repository cannot hold a tag: give {repo} a first commit, a README)") from exc


def upload(path, version, secret, replace=False, repo=None, base_url=None, opener=urllib.request.urlopen):
    """Uploads the installer as an asset of the Release `v<version>`, streamed; returns the public address GitHub gives it. An asset of that name already there is an error, unless `replace`."""
    release = release_of(version, secret, repo=repo, base_url=base_url, opener=opener)
    name = path.name
    for asset in [a for a in release.get("assets", []) if a.get("name") == name]:
        if not replace:
            raise PublishError(f"the Release {tag(version)} already has {name}: `--replace` deletes it and uploads this one")
        call("DELETE", f"{API}/repos/{repo or repository()}/releases/assets/{asset['id']}", secret, opener=opener)
    target = release["upload_url"].split("{", 1)[0] + "?name=" + urllib.parse.quote(name)
    with open(path, "rb") as body:
        try:
            answer = call("POST", target, secret, body=body, size=path.stat().st_size, opener=opener)
        except Refused as exc:
            raise PublishError(str(exc)) from exc
    return answer.get("browser_download_url", "")


def record(data, entry, name, size, digest, url, today=None):
    """The entry with the installer written in -- where it is kept, and its address -- and its date where it had none. Changes `data` and returns it."""
    entry["installer"] = {"file": name, "size": size, "sha256": digest, "hosted": "github", "url": url}
    entry.setdefault("date", (today or datetime.date.today()).isoformat())
    return data


def write_releases(data, path=None):
    path = path or RELEASES
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    temporary = Path(path).with_name(Path(path).name + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Publish a built installer as an asset of a Release of Woodcore's public releases repository on GitHub and record it in website/releases.json.")
    parser.add_argument("--version", help="the version to publish (default: calc/project.py's VERSION)")
    parser.add_argument("--dry-run", action="store_true", help="say what would be sent, send nothing, write nothing")
    parser.add_argument("--replace", action="store_true", help="delete the asset of that name the Release already has, then upload this one")
    args = parser.parse_args(argv)
    try:
        version = args.version or current_version()
        name = installer_name(version)
        path = DIST / name
        if not path.is_file():
            raise PublishError(f"{path} does not exist: build it first (python packaging/build.py)")
        data = load_releases()
        entry = entry_for(data, version)
        size, digest = path.stat().st_size, sha256(path)
        url = asset_url(version, name)
        problem = address_problem(url)
        if problem:
            raise PublishError(f"{problem}: the installed program would refuse this installer, so it is not uploaded (calc/tools/updates.py INSTALLER_PREFIX, website/site.json releases_repo)")
        print(f"{name}: {size / 2**20:.1f} MB, SHA-256 {digest}")
        print(f"  -> {repository()}, Release {tag(version)}, {url}")
        if args.dry_run:
            print("dry run: nothing sent, nothing written")
            return 0
        given = upload(path, version, token(), replace=args.replace)
        if given != url:
            raise PublishError(f"uploaded, but GitHub gives the address {given!r}, not {url!r}: nothing is written into releases.json; look at the Release and tell the engineer")
        write_releases(record(data, entry, name, size, digest, url))
        print(f"uploaded, and {RELEASES.relative_to(ROOT)} records it. To publish the site with it:")
        print(f'  git add website/releases.json && git commit -m "Woodcore {version} published"')
        print("  git push")
        return 0
    except PublishError as exc:
        print(f"publish: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
