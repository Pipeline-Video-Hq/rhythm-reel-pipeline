"""23-Nov (PIPELINE_SPEED_PROMPT_AB.md, causes 2 + 3): tell a request that never left this Mac from one that may have been
received, and wait for the network instead of killing the row.

    not_sent(e)          True when the request certainly did not reach the server (DNS failure, connection refused,
                         network unreachable, TLS handshake failure). Such a request was not billed, so sending it again is safe.
    wait_for_network(u)  blocks until https://<host of u> answers anything (a cheap HEAD every 60 s); max 6 h.

A timeout AFTER the request was sent is never treated as not_sent: it may have been accepted (and billed)."""
import errno, socket, ssl, time, urllib.error, urllib.parse, urllib.request

CHECK_EVERY = 60
MAX_WAIT = 6 * 3600
_DOWN = {errno.ECONNREFUSED, errno.ENETUNREACH, errno.EHOSTUNREACH, errno.ENETDOWN, errno.EHOSTDOWN}


def not_sent(e):
    r = getattr(e, "reason", e)
    if isinstance(e, urllib.error.HTTPError):
        return False                       # the server answered
    if isinstance(r, socket.gaierror):     # 'nodename nor servname provided' (DNS)
        return True
    if isinstance(r, ConnectionRefusedError):
        return True
    if isinstance(r, ssl.SSLError) and not isinstance(r, ssl.SSLZeroReturnError):
        return True                        # handshake failed: no request body was sent
    if isinstance(r, OSError) and getattr(r, "errno", None) in _DOWN:
        return True
    return False


def wait_for_network(url, log=print):
    host = urllib.parse.urlsplit(url).netloc or url
    t0 = time.time(); n = 0
    while True:
        try:
            urllib.request.urlopen(urllib.request.Request(f"https://{host}/", method="HEAD"), timeout=20).close()
            ok = True
        except urllib.error.HTTPError:
            ok = True                      # any HTTP answer = the network is back
        except Exception:                  # noqa: BLE001
            ok = False
        if ok:
            if n:
                log(f"network back after {int(time.time() - t0)} s ({host})")
            return
        if time.time() - t0 > MAX_WAIT:
            raise RuntimeError(f"no network to {host} for {MAX_WAIT // 3600} h")
        if n % 5 == 0:
            log(f"no network to {host} - waiting (checked every {CHECK_EVERY} s, nothing is lost)")
        n += 1
        time.sleep(CHECK_EVERY)
