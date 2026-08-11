# Filled in once the GitHub repository exists (see setup instructions from Claude).
GITHUB_OWNER = ""
GITHUB_REPO = ""
ASSET_NAME = "RecSizeHelper.exe"


def is_configured() -> bool:
    return bool(GITHUB_OWNER and GITHUB_REPO)
