import socket
import ssl

DEFAULT_HOME = "file:///Users/ciaranobrien/minerva/minerva/minerva.html"


def parse_url(url):
    scheme, url = url.split("://", 1)
    if "/" not in url:
        url = url + "/"
    host, path = url.split("/", 1)
    return (scheme, host, "/" + path)


def request(url):
    (scheme, host, path) = parse_url(url)
    assert scheme in ["http", "https", "file"], "Unknown scheme {}".format(scheme)

    if scheme in ["http", "https"]:
        return web_request(scheme, host, path)
    return local_resource(path)


def local_resource(path):
    with open(path, "r") as file:
        file_contents = file.read()
    return None, file_contents


def web_request(scheme, host, path):

    port = 80 if scheme == "http" else 443

    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    s = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )
    s.connect((host, port))

    if scheme == "https":
        ctx = ssl.create_default_context()
        s = ctx.wrap_socket(s, server_hostname=host)

    s.send(
        (
            "GET {} HTTP/1.1\r\n".format(path)
            + "Host: {}\r\nConnection: close\r\nUser-Agent: minerva\r\n\r\n".format(
                host
            )
        ).encode("utf8")
    )
    response = s.makefile("r", encoding="utf8", newline="\r\n")

    statusline = response.readline()
    version, status, explanation = statusline.split(" ", 2)
    assert status == "200", "{}: {}".format(status, explanation)

    headers = {}
    while True:
        line = response.readline()
        if line == "\r\n":
            break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()

    assert "transfer-encoding" not in headers
    assert "content-encoding" not in headers

    body = response.read()
    s.close()

    return headers, body


def show(body):
    in_angle = False
    for c in body:
        if c == "<":
            in_angle = True
        elif c == ">":
            in_angle = False
        elif not in_angle:
            print(c, end="")


def load(url):
    headers, body = request(url or DEFAULT_HOME)
    show(body)


if __name__ == "__main__":
    import sys

    try:
        arg = sys.argv[1]
    except IndexError:
        arg = None
    load(arg)
