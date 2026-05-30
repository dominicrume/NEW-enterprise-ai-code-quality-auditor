"""manifest_deriver — heuristic feature/hallucination detection from code."""
from auditor.analyzers.manifest_deriver import derive


SPEC = {"features": [
    {"id": "auth.register"}, {"id": "auth.login"},
    {"id": "course.list"},   {"id": "course.view"},
]}


def test_detects_implemented_features_via_two_segment_tokens():
    code = {"files": {"main.py": (
        "from fastapi import FastAPI\napp = FastAPI()\n"
        "@app.post('/auth/register')\ndef register(): pass\n"
        "@app.post('/auth/login')\ndef login(): pass\n"
        "@app.get('/courses')\ndef list_courses(): pass\n"
        "@app.get('/courses/{cid}')\ndef view_course(cid): pass\n"
    )}}
    result = derive(SPEC, code)
    assert set(result["implemented"]) == {"auth.register", "auth.login",
                                          "course.list", "course.view"}
    assert result["hallucinated_endpoints"] == []


def test_flags_off_spec_endpoint_as_hallucinated():
    code = {"files": {"main.py": (
        "from fastapi import FastAPI\napp = FastAPI()\n"
        "@app.get('/health')\ndef health(): pass\n"
        "@app.post('/auth/login')\ndef login(): pass\n"
    )}}
    result = derive(SPEC, code)
    assert "auth.login" in result["implemented"]
    assert "/health" in result["hallucinated_endpoints"]


def test_empty_codebase_yields_nothing():
    assert derive(SPEC, {"files": {}}) == {"implemented": [], "hallucinated_endpoints": []}
