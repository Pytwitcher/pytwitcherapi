from test import docs_snippets


def test_api_requests_snippet(mock_session):
    docs_snippets.execute_snippet('customrequest.py')
