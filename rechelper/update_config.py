GITHUB_OWNER = "StundZow"
GITHUB_REPO = "rec-size-helper"
ASSET_NAME = "RecSizeHelper.exe"


def is_configured() -> bool:
    return bool(GITHUB_OWNER and GITHUB_REPO)
