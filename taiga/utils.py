def urljoin(*parts):
    return "/".join(part.strip("/") for part in parts)
