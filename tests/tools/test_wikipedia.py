import pytest
from unittest.mock import patch
from app.tools.wikipedia import get_wikipedia_summary


@patch("app.tools.wikipedia.requests.get")
def test_wikipedia_success(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "title": "Colosseum",
        "extract": "The Colosseum is an ancient amphitheatre in Rome.",
        "content_urls": {
            "desktop": {
                "page": "https://en.wikipedia.org/wiki/Colosseum"
            }
        }
    }

    result = get_wikipedia_summary("Colosseum")

    assert result["found"] is True
    assert result["title"] == "Colosseum"
    assert "amphitheatre" in result["summary"]
    assert result["source"] == "wikipedia"


@patch("app.tools.wikipedia.requests.get")
def test_wikipedia_not_found(mock_get):
    mock_get.return_value.status_code = 404

    result = get_wikipedia_summary("NonExistingPlace123")

    assert result["found"] is False
    assert result["summary"] is None
    assert result["source"] == "wikipedia"
