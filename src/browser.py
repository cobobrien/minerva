import socket
import ssl
import re
import zlib

DEFAULT_HOME = "file:///Users/ciaranobrien/minerva/minerva/minerva.html"
REDIRECT_LIMIT = 5


def parse_url(url):
    scheme, url = url.split("://", 1)
    if "/" not in url:
        url = url + "/"
    host, path = url.split("/", 1)
    return (scheme, host, "/" + path)


def parse_data_schema_request(url):
    base_scheme, encoding, value = re.split(r"[:,]", url)
    return encoding, value


def request(url):
    if url.startswith("data"):
        return data_schema_request(*parse_data_schema_request(url))
    (scheme, host, path) = parse_url(url)
    assert scheme in ["http", "https", "file"], "Unknown scheme {}".format(scheme)

    if scheme in ["http", "https"]:
        return web_request(scheme, host, path)
    return local_resource(path)


def local_resource(path):
    with open(path, "r") as file:
        file_contents = file.read()
    return None, file_contents


def data_schema_request(encoding, value):
    html_response = f"""
    <html>
    <head></head>
    <body>{value}</body>
    </html>
    """
    if encoding == "text/html":
        return None, html_response


def web_request(scheme, host, path):

    redirects = 0
    while redirects < REDIRECT_LIMIT:

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
                + "Host: {}\r\nConnection: close\r\nUser-Agent: minerva\r\nAccept-Encoding: gzip\r\n\r\n".format(
                    host
                )
            ).encode("utf8")
        )
        response = s.makefile("rb", newline="\r\n")

        statusline = response.readline().decode("utf8")

        version, status, explanation = statusline.split(" ", 2)

        headers = {}
        while True:
            line = response.readline().decode("utf8")
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            headers[header.lower()] = value.strip()

        if int(status) >= 300:
            redirects += 1
            (scheme, host, path) = parse_url(headers["location"])
        elif int(status) >= 200:
            break

    if "transfer-encoding" in headers and headers["transfer-encoding"] == "chunked":
        chunks = []

        while True:
            chunk_len = response.readline().decode("utf8")
            chunk_len.replace("\r\n", "")
            chunk_len = int(chunk_len, 16)
            chunk = response.read(chunk_len)
            chunks.append(chunk)
            response.readline()
            if chunk_len == 0:
                break

        body = b"".join(chunks)
    else:
        # The rest of the response is the body of the request
        body = response.read()

    # body = response.read()

    if "content-encoding" in headers and headers["content-encoding"] == "gzip":
        # The response body is gzipped, decompress it *before* decoding it
        body = zlib.decompressobj(32).decompress(body).decode("utf8")
    else:
        body = body.decode("utf8")

    s.close()

    return headers, body


def transform(html):
    transformed_html = ""
    for c in html:
        if c == "<":
            transformed_html += "&lt;"
        elif c == ">":
            transformed_html += "&gt;"
        else:
            transformed_html += c
    return f"<body>{transformed_html}</body>"


def show(body):
    in_angle = False
    inside_body = False
    tag_name = ""
    entity_buffer = ""

    for c in body:
        if c == "<":
            in_angle = True
            tag_name = ""
            entity_buffer = ""
        elif c == ">":
            in_angle = False
            if tag_name == "body":
                inside_body = True
            elif tag_name == "/body":
                inside_body = False
        elif c == "&" and not entity_buffer:
            entity_buffer = "&"
        elif entity_buffer:
            entity_buffer += c
            if c == ";":
                if entity_buffer == "&lt;":
                    print("<", end="")
                elif entity_buffer == "&gt;":
                    print(">", end="")
                else:
                    print(entity_buffer, end="")
                entity_buffer = ""
        elif in_angle:
            tag_name += c
        elif inside_body:
            print(c, end="")


def load(url):
    if url.startswith("view-source:"):
        _, resource_url = url.split("view-source:")
        headers, body = request(resource_url)
        show(transform(body))
        return
    headers, body = request(url or DEFAULT_HOME)
    show(body)


if __name__ == "__main__":
    import sys

    try:
        arg = " ".join(sys.argv[1:])
    except IndexError:
        arg = None
    load(arg)
