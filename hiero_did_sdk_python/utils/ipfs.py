import json

from .http import fetch

DEFAULT_IPFS_HTTP_PROXY = "https://ipfs.io/ipfs/"


async def download_ipfs_document_by_cid(cid: str, ipfs_http_proxy: str = DEFAULT_IPFS_HTTP_PROXY) -> dict:
    url = f"{ipfs_http_proxy}/{cid}"
    return await download_ipfs_document_by_url(url)


async def download_ipfs_document_by_url(url: str) -> dict:
    try:
        document_json = await fetch(url)
        return json.loads(document_json)
    except Exception as error:
        raise Exception(f"DID document could not be fetched from URL: {url}") from error
