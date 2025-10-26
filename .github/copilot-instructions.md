
# GitHub Copilot Instructions


 1.   A small, stateful mock API service  (you create it;  we won’t provide one).  2.   Exactly two deep tests  (or one if you choose to merge  scenarios)—each test covers  multiple assertions and edge cases for the endpoints below.  Use Python + Pytest for tests 
 Why This Exercise (What we’re evaluating) 
 ●   Test design & depth:  Can you encode tricky product  rules into robust tests with clear  assertions?  ●   Reliability under concurrency:  Can your tests remain  stable even with parallel  requests and race conditions? 
 ●   Correctness & observability:  Make sure failures are easy to debug (good messages, logs,  structure)  ●   Maintainability:  Make it easy for others to extend your tests  (fixtures, helpers, parametrization)  ●   Pragmatism:  Choose simple, sensible designs  that get the job done
 API Slice (Spec You Must Implement in Your Mock) 
 You only need these endpoints and behaviors. Persist state  in memory  while the process runs. 
 1)  POST /applications  — Idempotent Create 
 Headers 
 ●   Authorization: Bearer <token> 
 ●   Idempotency-Key: <uuid>  (required) 
 Body 
 ●   { "name": "string", "description": "string (<=256, optional)" } 
 Rules 
 ●   name  must be  unique  after  trim + case-fold  (e.g.,  " My-App "  conflicts with 
 "my-app"  ).  ●   The same  Idempotency-Key  (for the same token)  must  return the original response 
 (do not create another resource).  ●   Rate limit:  Max  5 create attempts per minute per token  →  429 Too Many  Requests  +  Retry-After  (seconds). 
 Success (201) response 
 ●   { 
 ●   "id": "uuid", 
 ●   "name": "string", 
 ●   "description": "string|null", 
 ●   "is_active": false, 
 ●   "version": 1, 
 ●   "etag": "\"<opaque>\"", 
 ●   "created_at": "ISO-8601" 
 ●   } 
 Possible errors:  409 Conflict  (name not unique),  429  Too Many Requests  . 
 2)  PATCH /applications/{id}  — JSON Merge Patch with  Optimistic  Locking 
 Headers 
 ●   Authorization: Bearer <token> 
 ●   If-Match: "<etag>"  or  If-Match: W/"<version>"  (required) 
 Body (RFC 7396 merge patch) 
 ●   { 
 ●   "name": "string (optional)", 
 ●   "description": "string|null (optional)", 
 ●   "is_active": true|false (optional) 
 ●   } 
 Rules 
 ●   Validate  If-Match  . On success, increment  version  and  update  etag  .  ●   name  uniqueness as above (trim + case-fold). 
 ●   Business rule: If  name  contains  "test"  (any case), then  is_active: true  is 
 blocked  unless query param  ?force=true  is present  →  422 Unprocessable  Entity  with error code  NAME_FORBIDS_ACTIVATION  .  ●   Eventual consistency for activation:  On  is_active:  true  , your mock may:  ○   Return  200 OK  with  "is_active": true  immediately  ,  or 
 ○   Return  202 Accepted  with  { "status": "activating"  }  , and within ~2  seconds a  GET /applications/{id}  should reflect  "is_active":  true  . 
 Possible errors:  412 Precondition Failed  (stale/missing  If-Match  ),  409 Conflict 
 (name),  422 Unprocessable Entity  (business rule). 
 Optional helper endpoint:  GET /applications/{id}  to  verify state. 
 Your Deliverables 
 ●   mock_api/  — your mock server code and run instructions  ●   tests/  — your automated tests (Pytest preferred)  ●   README.md  — how to run the mock, how to run tests,  and a short explanation of your  design choices  ●   (Optional)  CI that runs tests and produces JUnit/HTML  report 
 The Two Deep Tests (What we expect your tests to  prove) 
 You can write these as two tests in one file or separate files. Each test can include  sub-steps and helper functions. 
 Test 1 — Idempotent Create under Concurrency & Rate Limits 
 Goal:  Prove robust idempotency and respectful retry behavior. 
 What to assert 
 1.   Concurrency/idempotency 
 ○   Send N parallel  POST /applications  with the  same  Idempotency-Key  and  identical payload.  ○   Assert that  exactly one  resource is created and  all  successful responses  share the same  id  and body  .  2.   Rate limiting 
 ○   Make  >5 distinct creates  within a minute using  unique  idempotency keys.  ○   Expect at least one  429  with a valid  Retry-After  integer.  ○   Implement a retry that  honors  Retry-After  and eventually  succeeds (without  violating idempotency).  3.   Negative idempotency 
 ○   Send a second request with the  same  Idempotency-Key  but a  different  payload  (e.g., different  name  ).  ○   Assert the server still returns the  original response  (no second resource  created). 
 What we’re looking for 
 ●   Stable concurrency handling (threads/async), deterministic assertions, clear logs.  ●   Correct interpretation of  Retry-After  and backoff. 
 Test 2 — Optimistic Locking, Normalization, and Conditional Activation 
 Goal:  Exercise ETag/version control, normalized uniqueness,  and activation rules with eventual  consistency. 

 What to assert in tests
1. Normalization & uniqueness
○ Create app with name=" My-App ".
○ Attempt to rename another app to "my-app" → expect 409 Conflict
(normalized collision).
2. Two-writer race with If-Match
○ Fetch current etag/version.
○ Run two concurrent PATCHes with the same If-Match:
■ One should succeed; the other should get 412 Precondition
Failed.
3. Activation rule
○ Rename app to include "Test" (e.g., "My-App-Test").
○ PATCH is_active: true without ?force=true → expect 422 with code
NAME_FORBIDS_ACTIVATION.
○ Retry with ?force=true:
■ If 200, assert "is_active": true.
■ If 202, poll GET /applications/{id} with bounded retries (≤ ~2.5s
total) until "is_active": true.
4. Atomicity
○ Send one PATCH changing both name (to a conflicting value) and is_active.
○ Assert the entire patch is rejected (no partial apply; resource remains
unchanged).
What we’re looking for
● Proper use of If-Match and clean handling of stale preconditions.
● Bounded polling strategy for eventual consistency (no infinite waits).
● Explicit checks for no partial updates on error.
Implementation Guidance (to help you succeed)
Minimum Requirements for the Mock
● In-memory store for applications, versions, etags, and idempotency records scoped
by token.
● Rate limiter per token (5/min). Return 429 and a realistic Retry-After.
● Deterministic or configurable activation mode:
○ ACTIVATION_MODE=immediate|eventual
○ ACTIVATION_DELAY_MS=1500 (if eventual)
● Basic logging: method, path, Idempotency-Key, If-Match, status, and timings.
Suggested Project Structure
● /mock_api
● app.(py|js|…)
● requirements.txt|package.json
● README.md
● /tests
● test_idempotent_create.py
● test_patch_optimistic_locking.py
● conftest.py # fixtures: base_url, auth token, http client,
retry helpers
● README.md
Test Quality Tips
● Prefer fixtures for setup/teardown and configuration (base URL, token).
● Add a small retry_until(predicate, timeout, interval) helper and a
respect_retry_after(response) helper.
● Make assertion messages descriptive (include method, path, status, and the relevant
IDs).
● Keep tests independent (each sets up its own data).
Assumptions You May Make
● Treat the token as an opaque string; no need to validate its structure.
● Idempotency-Key format: treat as GUID/UUID-like, but validation can be minimal.
● You don’t need pagination, listing endpoints, or delete—only what’s specified above.
Submission Checklist
● I can start the mock API locally with a clear command.
● Tests run with a single command (e.g., pytest -q).
● README explains decisions, assumptions, and how to toggle activation mode.
● Tests include concurrency, rate limit handling, If-Match race, normalization
collision, and activation rule.
● Logs/outputs are readable in CI or locally.
● (Optional) CI workflow + test report artifact.

Additional points to consider:
Focus on testing. The mock is a means to create realistic behaviors; keep it simple but correct.
support the provided fields and semantics accurately no need to implement a full RFC-compliant JSON Merge Patch parser
