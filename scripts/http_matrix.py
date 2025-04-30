from fastapi import APIRouter, HTTPException

router = APIRouter()

# ----------------------------
# 401 Unauthorized
# ----------------------------
@router.get("/api/unauthorized")
@router.get("/api/gdd/unauthorized")
@router.get("/api/weather/unauthorized")
def fake_unauthorized():
    raise HTTPException(status_code=401, detail="You must log in.")

# ----------------------------
# 403 Forbidden
# ----------------------------
@router.get("/api/forbidden")
@router.get("/api/gdd/forbidden")
@router.get("/api/weather/forbidden")
def fake_forbidden():
    raise HTTPException(status_code=403, detail="Access denied.")

# ----------------------------
# 400 Bad Request
# ----------------------------
@router.get("/api/bad_request")
@router.get("/api/gdd/bad_request")
@router.get("/api/weather/bad_request")
def fake_bad_request():
    raise HTTPException(status_code=400, detail="Bad format.")

# ----------------------------
# 422 Unprocessable Entity
# ----------------------------
@router.get("/api/unprocessable")
@router.get("/api/gdd/unprocessable")
@router.get("/api/weather/unprocessable")
def fake_unprocessable():
    raise HTTPException(status_code=422, detail="Invalid data")

# ----------------------------
# 500 Internal Server Error
# ----------------------------
@router.get("/api/server_error")
@router.get("/api/gdd/server_error")
@router.get("/api/weather/server_error")
def fake_server_error():
    raise HTTPException(status_code=500, detail="Server broke down")
# ----------------------------