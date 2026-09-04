"""Vmake-API-Client (geteiltes Tool, geboren aus 033 SA) (Caption-/Text-Entfernung aus Video, Task videoscreenclear).

Eigenimplementierung des dokumentierten SDK-HMAC-SHA256-Schemas (Signatur-Spezifikation
aus dem offiziellen Vmake-SDK gelesen, Code selbst geschrieben — kein Fremdcode ausgeführt).
Flow: config → (Video-URL bereitstellen) → consume (Quota) → invoke → poll → output_urls.

Usage: vmake_client.py config | remove <video_url> | poll <task_id>
Keys: VMAKE_AK / VMAKE_SK aus ~/.config/leichtkraut/.env
"""
import datetime
import hashlib
import hmac
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request
from urllib.parse import urlparse, parse_qs, urlencode

WAPI = "wapi-skill.vmake.ai"
ALGO = "SDK-HMAC-SHA256"
UA = "vmake-sdk-python/1.0"
STATE = os.path.join(os.getcwd(), "vmake_state.json")  # im Projekt-Ordner ausführen


def _keys():
    ak = sk = None
    env = os.path.expanduser("~/.config/leichtkraut/.env")
    for line in open(env):
        if line.startswith("VMAKE_AK="):
            ak = line.split("=", 1)[1].strip()
        if line.startswith("VMAKE_SK="):
            sk = line.split("=", 1)[1].strip()
    if not ak or not sk:
        raise RuntimeError("VMAKE_AK/VMAKE_SK fehlen in ~/.config/leichtkraut/.env")
    return ak, sk


def sign(url, method, headers, body, ak, sk):
    """SDK-HMAC-SHA256: CanonicalRequest → StringToSign → HMAC; Header-Wert base64 + 'Bearer '."""
    t = datetime.datetime.now(datetime.timezone.utc)
    xdate = t.strftime("%Y%m%dT%H%M%SZ")
    headers = dict(headers)
    headers["X-Sdk-Date"] = xdate
    p = urlparse(url)
    canonical_uri = p.path if p.path.endswith("/") else p.path + "/"
    canonical_query = urlencode(sorted(parse_qs(p.query).items()), doseq=True)
    signed = sorted(k.lower() for k in headers)
    low = {k.lower(): v.strip() for k, v in headers.items()}
    canonical_headers = "\n".join(f"{k}:{low[k]}" for k in signed)
    body_hash = hashlib.sha256(body.encode()).hexdigest()
    creq = f"{method}\n{canonical_uri}\n{canonical_query}\n{canonical_headers}\n{';'.join(signed)}\n{body_hash}"
    sts = f"{ALGO}\n{xdate}\n{hashlib.sha256(creq.encode()).hexdigest()}"
    sig = hmac.new(sk.encode(), sts.encode(), hashlib.sha256).hexdigest()
    header_value = f"{ALGO} Access={ak}, SignedHeaders={';'.join(signed)}, Signature={sig}"
    headers["Authorization"] = "Bearer " + base64.b64encode(header_value.encode()).decode()
    return headers


def call(url, method="GET", body=None, timeout=60):
    ak, sk = _keys()
    host = urlparse(url).netloc
    headers = {"Host": host, "User-Agent": UA}
    body_str = json.dumps(body) if body else ""
    if body:
        headers["Content-Type"] = "application/json"
    headers = sign(url, method, headers, body_str, ak, sk)
    req = urllib.request.Request(url, data=body_str.encode() if body_str else None,
                                 method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_body": e.read().decode("utf-8", "replace")[:500]}


def load_state():
    return json.load(open(STATE)) if os.path.exists(STATE) else {}


def save_state(st):
    json.dump(st, open(STATE, "w"), ensure_ascii=False, indent=1)


def wapi_config():
    st = load_state()
    r = call(f"https://{WAPI}/skill/config.json", "POST",
             {"gid": st.get("gid", ""), "version": "v1.0.0"})
    meta = (r.get("meta") or {})
    if meta.get("code") not in (0, "0", None):
        print("CONFIG-FEHLER:", json.dumps(r, ensure_ascii=False)[:600])
        sys.exit(1)
    resp = r.get("response") or {}
    if resp.get("gid"):
        st["gid"] = resp["gid"]
    algo = resp.get("algorithm") or {}
    st["regions"] = algo.get("regions") or st.get("regions") or {}
    st["token_policy_type"] = algo.get("token_policy_type") or st.get("token_policy_type") or "mtai"
    st["token_policy_types"] = algo.get("token_policy_types") or st.get("token_policy_types")
    st["invoke"] = algo.get("invoke") or st.get("invoke") or {}
    save_state(st)
    print(f"CONFIG OK · gid={st.get('gid','')[:12]}… · regions={list(st['regions'].keys())} · "
          f"invoke-Tasks={sorted(st['invoke'].keys())}")
    return st


def _token_policy_raw(st, typ_name):
    region = "cn-north-4" if "cn-north-4" in st["regions"] else next(iter(st["regions"]))
    endpoint = st["regions"][region]
    types_map = st.get("token_policy_types") or {}
    typ = types_map.get(typ_name) or st.get("token_policy_type", "mtai")
    r = call(f"https://{endpoint}/ai/token_policy?type={typ}")
    if (r.get("meta") or {}).get("code") not in (0, "0", None):
        print("TOKEN-POLICY-FEHLER:", json.dumps(r, ensure_ascii=False)[:400]); sys.exit(1)
    return r.get("data") or (r.get("response") or {}).get("data") or r.get("response") or {}


def token_policy(st, typ_name):
    """AI-(Algorithmus-)Strategie: mtai.api[order[0]]."""
    d = _token_policy_raw(st, typ_name)
    cloud = d["mtai"]["api"]["order"][0]
    return d["mtai"]["api"][cloud]


def upload_policy(st):
    """OSS-Upload-Strategie: mtai.upload[order[0]] (frische creds + key + Ergebnis-URL)."""
    d = _token_policy_raw(st, "upload")
    up = d["mtai"]["upload"]
    return up[up["order"][0]]


def oss_put(pol, file_path, content_type="video/mp4"):
    """Datei per Alibaba-OSS-V1-Signatur (HMAC-SHA1, STS-Token) hochladen → Ergebnis-URL.
    Selbst implementiert nach OSS-Signaturspezifikation — keine Fremd-Lib nötig."""
    import email.utils
    creds = pol["credentials"]
    ak, sk, token = creds["access_key"], creds["secret_key"], creds.get("session_token", "")
    bucket, key = pol["bucket"], pol["key"]
    host = urlparse(pol["url"]).netloc  # oss-ap-southeast-1.aliyuncs.com
    date = email.utils.formatdate(usegmt=True)
    canon_headers = f"x-oss-security-token:{token}\n" if token else ""
    canon_resource = f"/{bucket}/{key}"
    sts = f"PUT\n\n{content_type}\n{date}\n{canon_headers}{canon_resource}"
    import hashlib as _h
    sig = base64.b64encode(hmac.new(sk.encode(), sts.encode(), _h.sha1).digest()).decode()
    body = open(file_path, "rb").read()
    put_url = f"https://{bucket}.{host}/{key}"
    headers = {"Host": f"{bucket}.{host}", "Date": date, "Content-Type": content_type,
               "Authorization": f"OSS {ak}:{sig}", "Content-Length": str(len(body))}
    if token:
        headers["x-oss-security-token"] = token
    req = urllib.request.Request(put_url, data=body, method="PUT", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            if r.status not in (200, 203):
                raise RuntimeError(f"OSS PUT status {r.status}")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"OSS PUT {e.code}: {e.read().decode('utf-8','replace')[:400]}")
    return pol["data"]


def cmd_remove(video_arg):
    st = wapi_config()
    task = "videoscreenclear"
    spec = st["invoke"].get(task) or {}
    print(f"invoke-Preset {task}: {json.dumps(spec, ensure_ascii=False)[:300]}")
    # Lokale Datei → zu Vmakes eigenem OSS hochladen (China-Server erreicht Fremd-Hosts nicht);
    # http(s)-Argument wird direkt durchgereicht.
    if os.path.isfile(video_arg):
        pol = upload_policy(st)
        print(f"OSS-Upload → bucket={pol['bucket']} ({pol['url']}) …", flush=True)
        video_url = oss_put(pol, video_arg)
        print("OSS-URL:", video_url[:80])
    else:
        video_url = video_arg
    # Quota
    r = call(f"https://{WAPI}/skill/consume.json", "POST",
             {"url": video_url, "task": task, "gid": st.get("gid", "")})
    if (r.get("meta") or {}).get("code") not in (0, "0", None):
        print("CONSUME-VERWEIGERT:", json.dumps(r, ensure_ascii=False)[:500]); sys.exit(1)
    context = (r.get("response") or {}).get("context", "")
    print("Quota OK, context:", (context or "")[:60])
    # Algorithmus-Job
    policy = token_policy(st, "ai")
    host = policy["url"].split("://", 1)[-1]
    payload = {"params": json.dumps(spec.get("params") or {}), "context": context,
               "task": spec.get("task", task), "task_type": spec.get("task_type") or "mtlab",
               "sync_timeout": policy["sync_timeout"], "init_images": [{"url": video_url}]}
    r = call(policy["url"] + "/" + policy["push_path"], "POST", payload,
             timeout=int(policy["sync_timeout"]) + 15)
    print("SUBMIT:", json.dumps(r, ensure_ascii=False)[:400])
    data = r.get("data") or {}
    if data.get("status") == 9:
        tid = data["result"]["id"]
        st["task_id"] = str(tid); st["policy"] = policy; save_state(st)
        print(f"ASYNC task_id={tid} → poll mit: vmake_client.py poll {tid}")
    else:
        urls = _outputs(r)
        print("SYNC-ERGEBNIS output_urls:", urls)


def _outputs(body):
    out, seen = [], set()
    def add(v):
        if isinstance(v, str) and v.startswith("http") and v not in seen:
            seen.add(v); out.append(v)
        elif isinstance(v, list):
            for x in v: add(x)
    res = ((body.get("data") or {}).get("result")) or {}
    for k in ("urls", "images", "videos", "url"):
        add(res.get(k))
    for mil in (res.get("media_info_list"),
                ((res.get("data") or {}).get("media_info_list") if isinstance(res.get("data"), dict) else None),
                ((res.get("mtlab_res") or {}).get("media_info_list") if isinstance(res.get("mtlab_res"), dict) else None)):
        if isinstance(mil, list):
            for it in mil:
                if isinstance(it, dict): add(it.get("media_data"))
    return out


def cmd_poll(tid):
    st = load_state()
    policy = st.get("policy") or token_policy(st, "ai")
    uri = policy["url"] + "/" + policy["status_query"]["path"] + "?task_id=" + tid
    t0 = time.time()
    while time.time() - t0 < 540:
        r = call(uri)
        data = r.get("data") or {}
        s = data.get("status")
        if s in (10, 2, 20):
            urls = _outputs(r)
            print("FERTIG · output_urls:", urls)
            st["output_urls"] = urls; save_state(st)
            return
        if s == 3 or (r.get("meta") or {}).get("code") not in (0, "0", None):
            print("FEHLGESCHLAGEN:", json.dumps(r, ensure_ascii=False)[:500]); sys.exit(1)
        print(f"… status={s} ({time.time()-t0:.0f}s)", flush=True)
        time.sleep(12)
    print("TIMEOUT — weiter pollen mit: vmake_client.py poll", tid); sys.exit(2)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "config":
        wapi_config()
    elif cmd == "remove":
        cmd_remove(sys.argv[2])
    elif cmd == "poll":
        cmd_poll(sys.argv[2])


def cmd_download(dest):
    st = load_state()
    urls = st.get("output_urls") or []
    if not urls:
        print("Keine output_urls im State — erst remove/poll laufen lassen."); sys.exit(1)
    subprocess.run(["curl", "-sL", "--max-time", "600", "-o", dest, urls[0]], check=True)
    print(f"Heruntergeladen → {dest}")


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "download":
    cmd_download(sys.argv[2])
