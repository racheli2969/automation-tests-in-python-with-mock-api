import uuid
from datetime import datetime
import asyncio
from fastapi import APIRouter, HTTPException, Header, Request, Response
from fastapi.responses import JSONResponse

from ..models.application import ApplicationCreate, Application
from ..services.application_service import ApplicationService, RateLimiter, IdempotencyService
from ..config.settings import ACTIVATION_MODE, ACTIVATION_DELAY_MS

router = APIRouter()
application_service = ApplicationService()
rate_limiter = RateLimiter()
idempotency_service = IdempotencyService()

# rules for idempotent create:
#     name must be unique after trim + case-fold (e.g., " My-App " conflicts with
# "my-app").
# ● The same Idempotency-Key (for the same token) must return the original response
# (do not create another resource).
# ● Rate limit: Max 5 create attempts per minute per token → 429 Too Many
# Requests + Retry-After (seconds).
# Possible errors: 409 Conflict (name not unique), 429 Too Many Requests
@router.post("/applications", status_code=201)
async def create_application(
    request: Request,
    application: ApplicationCreate,
    authorization: str = Header(...),
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    token = authorization.replace("Bearer ", "")
    
    # Check rate limit
    allowed, retry_after = rate_limiter.check_rate_limit(token)
    if not allowed:
        return JSONResponse(
            status_code=429,
            headers={"Retry-After": str(retry_after)},
            content={"error": "Too many requests"}
        )
    
    # Check idempotency
    existing_response = idempotency_service.get_record(token, idempotency_key)
    if existing_response:
        return existing_response
    
    # Validate name uniqueness
    if not application_service.is_name_unique(application.name):
        raise HTTPException(status_code=409, detail="Application name already exists")
    
    # Create application
    app_id = str(uuid.uuid4())
    version = 1
    app_data = {
        "id": app_id,
        "name": application.name,
        "description": application.description,
        "is_active": False,
        "version": version,
        "created_at": datetime.now().isoformat()
    }
    app_data["etag"] = application_service.generate_etag(version, app_data)
    
    application_service.create_application(app_id, app_data)
    response_data = Application(**app_data)
    response = JSONResponse(status_code=201, content=response_data.dict())
    
    # Store idempotency record
    idempotency_service.store_record(token, idempotency_key, response)
    
    return response


# rules for  patch
# Validate If-Match. On success, increment version and update etag.
# ● name uniqueness as above (trim + case-fold).
# Business rule: If name contains "test" (any case), then is_active: true is
# blocked unless query param ?force=true is present → 422 Unprocessable
# Entity with error code NAME_FORBIDS_ACTIVATION.
# ● Eventual consistency for activation: On is_active: true, your mock may:
# ○ Return 200 OK with "is_active": true immediately, or
# ○ Return 202 Accepted with { "status": "activating" }, and within ~2
# seconds a GET /applications/{id} should reflect "is_active": true.
# Possible errors: 412 Precondition Failed (stale/missing If-Match), 409 Conflict
# (name), 422 Unprocessable Entity (business rule).
@router.patch("/applications/{app_id}")
async def update_application(
    app_id: str,
    request: Request,
    if_match: str = Header(..., alias="If-Match"),
    authorization: str = Header(...),
    force: bool = False
):
    token = authorization.replace("Bearer ", "")
    
    # Check if application exists
    app_data = application_service.get_application(app_id)
    if not app_data:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Validate If-Match
    if if_match.startswith('W/"'):
        version = int(if_match.strip('W/"'))
        if version != app_data["version"]:
            raise HTTPException(status_code=412, detail="Precondition failed")
    else:
        if if_match != app_data["etag"]:
            raise HTTPException(status_code=412, detail="Precondition failed")
    
    # Parse patch data
    patch_data = await request.json()
    
    # Create updated data
    updated_data = app_data.copy()
    if "name" in patch_data:
        if not application_service.is_name_unique(patch_data["name"], app_id):
            raise HTTPException(status_code=409, detail="Application name already exists")
        updated_data["name"] = patch_data["name"]
    
    if "description" in patch_data:
        updated_data["description"] = patch_data["description"]
    
    if "is_active" in patch_data:
        # Check test name activation rule
        if (
            patch_data["is_active"]
            and "test" in application_service.normalize_name(updated_data["name"])
            and not force
        ):
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "NAME_FORBIDS_ACTIVATION",
                    "message": "Cannot activate application with 'test' in name without force flag"
                }
            )
        
        if patch_data["is_active"] and ACTIVATION_MODE == "eventual":
            # Return 202 Accepted for eventual consistency
            updated_data["version"] += 1
            updated_data["etag"] = application_service.generate_etag(updated_data["version"], updated_data)
            application_service.update_application(app_id, updated_data)
            
            async def activate_later():
                await asyncio.sleep(ACTIVATION_DELAY_MS / 1000)
                app_data = application_service.get_application(app_id)
                if app_data:
                    app_data["is_active"] = True
                    application_service.update_application(app_id, app_data)
            
            asyncio.create_task(activate_later())
            
            return JSONResponse(
                status_code=202,
                content={"status": "activating"}
            )
        else:
            updated_data["is_active"] = patch_data["is_active"]
    
    # Update version and etag
    updated_data["version"] += 1
    updated_data["etag"] = application_service.generate_etag(updated_data["version"], updated_data)
    
    # Save changes
    application_service.update_application(app_id, updated_data)
    
    return Application(**updated_data)


@router.get("/applications/{app_id}")
async def get_application(
    app_id: str,
    authorization: str = Header(...)
):
    app_data = application_service.get_application(app_id)
    if not app_data:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return Application(**app_data)