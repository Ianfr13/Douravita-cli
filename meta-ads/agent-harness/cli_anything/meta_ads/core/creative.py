"""Ad Creative management."""

from typing import Dict, List, Optional
from cli_anything.meta_ads.utils.meta_ads_backend import (
    api_get, api_post, api_delete, api_paginate, CREATIVE_FIELDS
)

CALL_TO_ACTION_TYPES = [
    "BOOK_TRAVEL", "BUY_NOW", "CALL_NOW", "CONTACT_US", "DONATE",
    "DOWNLOAD", "GET_DIRECTIONS", "GET_OFFER", "GET_QUOTE", "INSTALL_APP",
    "LEARN_MORE", "LIKE_PAGE", "MESSAGE_PAGE", "NO_BUTTON",
    "OPEN_LINK", "ORDER_NOW", "PLAY_GAME", "REQUEST_TIME",
    "SEE_MENU", "SEND_MESSAGE", "SHOP_NOW", "SIGN_UP",
    "SUBSCRIBE", "USE_APP", "WATCH_MORE", "WATCH_VIDEO",
]


def list_creatives(access_token: str, ad_account_id: str,
                   limit: int = 50) -> List[Dict]:
    return api_paginate(f"{ad_account_id}/adcreatives", access_token,
                        {"fields": CREATIVE_FIELDS, "limit": limit})


def get_creative(access_token: str, creative_id: str) -> Dict:
    return api_get(creative_id, access_token, {"fields": CREATIVE_FIELDS})


def create_creative(access_token: str, ad_account_id: str,
                    name: str, page_id: str,
                    message: str = None, link: str = None,
                    image_hash: str = None, video_id: str = None,
                    call_to_action_type: str = None,
                    link_description: str = None,
                    headline: str = None) -> Dict:
    """Create an ad creative.

    Supports link (image/video) creatives.  For image creatives, upload
    an image via the adimages endpoint first to get its hash.

    Args:
        page_id: Facebook Page ID the ad runs from.
        message: Primary ad text.
        link: Destination URL.
        image_hash: Hash of previously-uploaded image (from adimages).
        video_id: ID of previously-uploaded video.
        call_to_action_type: e.g. LEARN_MORE, SHOP_NOW, SIGN_UP.
        link_description: Text below the headline in link ads.
        headline: Headline text for link ads.
    """
    object_story_spec = {"page_id": page_id}

    if video_id:
        video_data = {}
        if message:
            video_data["message"] = message
        if link:
            video_data["link_description"] = link_description or link
        if call_to_action_type:
            video_data["call_to_action"] = {
                "type": call_to_action_type.upper(),
                "value": {"link": link} if link else {},
            }
        video_data["video_id"] = video_id
        object_story_spec["video_data"] = video_data
    else:
        link_data = {}
        if message:
            link_data["message"] = message
        if link:
            link_data["link"] = link
        if image_hash:
            link_data["image_hash"] = image_hash
        if headline:
            link_data["name"] = headline
        if link_description:
            link_data["description"] = link_description
        if call_to_action_type:
            link_data["call_to_action"] = {
                "type": call_to_action_type.upper(),
                "value": {"link": link} if link else {},
            }
        object_story_spec["link_data"] = link_data

    payload = {
        "name": name,
        "object_story_spec": object_story_spec,
    }
    return api_post(f"{ad_account_id}/adcreatives", access_token, payload)


def delete_creative(access_token: str, creative_id: str) -> Dict:
    return api_delete(creative_id, access_token)


def list_images(access_token: str, ad_account_id: str,
                limit: int = 50) -> List[Dict]:
    """List uploaded ad images (returns hash, name, url, etc.)."""
    fields = "hash,name,url,width,height,created_time"
    return api_paginate(f"{ad_account_id}/adimages", access_token,
                        {"fields": fields, "limit": limit})


def upload_image(access_token: str, ad_account_id: str,
                 image_path: str) -> Dict:
    """Upload an image file and return its hash for use in creatives."""
    import requests
    from cli_anything.meta_ads.utils.meta_ads_backend import (
        GRAPH_BASE_URL, _raise_if_error
    )
    url = f"{GRAPH_BASE_URL}/{ad_account_id}/adimages"
    with open(image_path, "rb") as img:
        resp = requests.post(
            url,
            data={"access_token": access_token},
            files={"filename": img},
            timeout=60,
        )
    resp.raise_for_status()
    data = resp.json()
    _raise_if_error(data)
    # Response: {"images": {"filename": {"hash": "...", "url": "..."}}}
    images = data.get("images", {})
    for _fname, info in images.items():
        return info
    return data
