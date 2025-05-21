from fastapi import APIRouter, HTTPException

router = APIRouter()


# 401 Unauthorized
@router.get("/unauthorized/")
@router.get("/gdd/unauthorized/")
@router.get("/weather/unauthorized/")
def unauthorized_response():
    raise HTTPException(status_code=401, detail="You must log in.")


# 403 Forbidden
@router.get("/forbidden/")
@router.get("/gdd/forbidden/")
@router.get("/weather/forbidden/")
def forbidden_response():
    raise HTTPException(status_code=403, detail="Access denied.")


# 400 Bad Request
@router.get("/bad_request/")
@router.get("/gdd/bad_request/")
@router.get("/weather/bad_request/")
def bad_request_response():
    raise HTTPException(status_code=400, detail="Bad format.")


# 422 Unprocessable Entity
@router.get("/unprocessable/")
@router.get("/gdd/unprocessable/")
@router.get("/weather/unprocessable/")
def unprocessable_response():
    raise HTTPException(status_code=422, detail="Invalid data.")


# 500 Internal Server Error
@router.get("/server_error/")
@router.get("/gdd/server_error/")
@router.get("/weather/server_error/")
def server_error_response():
    raise HTTPException(status_code=500, detail="Server broke down.")
