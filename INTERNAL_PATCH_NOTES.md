# Internal Patch Notes

This file is for developers only. Do not link it from `README.md` or expose it in user-facing documentation.

## Purpose

This project is intentionally vulnerable. The notes below mark the main patch points that should be changed later when building a hardened version for comparison.

## Vulnerability Map

| ID | Vulnerable area | Current behavior | Patch focus | Main files |
|---|---|---|---|---|
| V1 | Blind SQL Injection | User-controlled input is inserted into SQL strings directly | Replace raw string-built SQL with parameterized queries and normalize failure handling | `app/src/routes/auth.py`, `app/src/routes/admin.py` |
| V2 | Stored XSS | Post and comment HTML is stored and rendered without sanitization | Escape by default, sanitize allowed markup if needed, remove unsafe template rendering | `app/src/routes/community.py`, `app/src/templates/community/detail.html` |
| V3 | IDOR | Resource ownership is not checked for profile, history, and file access | Enforce subject-resource ownership or admin-only override on each lookup path | `app/src/routes/main.py`, `app/src/routes/stocks.py`, `app/src/routes/wallet.py`, `app/src/routes/community.py` |
| V4 | Parameter Tampering | Server trusts client-supplied total values and transfer amounts | Recalculate sensitive amounts on server and validate range/sign/balance | `app/src/routes/stocks.py`, `app/src/services/stock_service.py`, `app/src/routes/wallet.py`, `app/src/services/transaction_service.py` |
| V5 | CSRF | State-changing POST routes accept requests without CSRF protection | Add CSRF token generation/validation for all mutating actions | `app/src/routes/wallet.py`, `app/src/routes/community.py`, related templates |
| V6 | Authorization weakness | Admin routes only require login and post edit/delete lacks ownership checks | Add role checks for admin endpoints and author checks for content mutation routes | `app/src/routes/admin.py`, `app/src/routes/community.py`, `app/src/templates/base.html` |
| V7 | File upload weakness | Uploaded files are accepted with minimal filtering and later served back | Add extension/MIME/content validation, safe storage policy, and download restrictions | `app/src/services/file_service.py`, `app/src/routes/community.py`, `app/src/static/uploads/` |

## Detailed Notes

### V1. Blind SQL Injection

#### Login flow

- Current patch target:
  - `app/src/routes/auth.py`
- Current vulnerable logic:
  - `login()` builds `SELECT * FROM users WHERE username = '{username}' LIMIT 1` using string interpolation.
- Hardened version should:
  - Convert to parameterized query.
  - Keep login failure responses uniform.
  - Consider rate limiting and audit logging separately from the SQLi fix.

#### Admin user search

- Current patch target:
  - `app/src/routes/admin.py`
  - `app/src/templates/admin/users.html`
- Current vulnerable logic:
  - `/admin/users?q=` builds a `LIKE '%{q}%'` query directly.
- Hardened version should:
  - Use placeholders for every search field.
  - Optionally constrain search length and accepted characters.

### V2. Stored XSS

#### Community post and comment rendering

- Current patch target:
  - `app/src/routes/community.py`
  - `app/src/templates/community/detail.html`
- Current vulnerable logic:
  - Post content and comment content are stored as submitted.
  - Template renders them with `|safe`.
- Hardened version should:
  - Remove `|safe` for untrusted content.
  - Sanitize on write or render if rich text is required.
  - Review file names shown in templates as untrusted output as well.

### V3. IDOR

#### Profile access

- Current patch target:
  - `app/src/routes/main.py`
- Current vulnerable logic:
  - `/mypage?user_id=` returns another user's profile with no ownership check.
- Hardened version should:
  - Restrict to `session["user_id"]` unless requester is admin.

#### Trade and wallet history access

- Current patch target:
  - `app/src/routes/stocks.py`
  - `app/src/routes/wallet.py`
- Current vulnerable logic:
  - `user_id` query string controls which records are shown.
- Hardened version should:
  - Bind history lookup to current session user by default.
  - Add explicit admin-only query support if cross-user lookup is needed.

#### File download access

- Current patch target:
  - `app/src/routes/community.py`
- Current vulnerable logic:
  - Any logged-in user can fetch any file by `file_id`.
- Hardened version should:
  - Verify that the requester owns the parent post or has admin privilege, depending on desired policy.
  - Avoid exposing predictable raw identifiers if possible.

### V4. Parameter Tampering

#### Stock buy and sell

- Current patch target:
  - `app/src/routes/stocks.py`
  - `app/src/services/stock_service.py`
- Current vulnerable logic:
  - `total_price` comes from the request and is used as the transaction amount.
- Hardened version should:
  - Load current stock price on server.
  - Recompute `total_price = current_price * quantity`.
  - Validate quantity bounds and selling limits server-side.

#### Wallet transfer

- Current patch target:
  - `app/src/routes/wallet.py`
  - `app/src/services/transaction_service.py`
- Current vulnerable logic:
  - Transfer amount is only parsed; negative and abnormal values are not rejected.
- Hardened version should:
  - Require positive integer amount.
  - Check sender balance before update.
  - Wrap balance changes in stricter transaction handling.

### V5. CSRF

#### State-changing routes

- Current patch target:
  - `app/src/routes/wallet.py`
  - `app/src/routes/community.py`
  - Templates for transfer, post edit/delete, and comment write
- Current vulnerable logic:
  - POST endpoints do not require CSRF token validation.
- Hardened version should:
  - Add CSRF tokens to forms.
  - Reject missing or invalid tokens.

### V6. Authorization Weakness

#### Admin endpoints

- Current patch target:
  - `app/src/routes/admin.py`
  - `app/src/templates/base.html`
- Current vulnerable logic:
  - Admin pages are hidden in UI for non-admin users, but server-side only checks login.
- Hardened version should:
  - Add a role-based decorator for admin-only routes.
  - Keep UI hiding as secondary, not primary, control.

#### Community content mutation

- Current patch target:
  - `app/src/routes/community.py`
- Current vulnerable logic:
  - Any logged-in user can edit or delete any post if they know the `post_id`.
- Hardened version should:
  - Require author ownership or admin override before edit/delete.

### V7. File Upload Weakness

#### Upload and storage path

- Current patch target:
  - `app/src/services/file_service.py`
  - `app/src/routes/community.py`
- Current vulnerable logic:
  - Uploaded file extension, MIME type, and content are not validated.
  - File names are only weakly normalized before saving.
- Hardened version should:
  - Restrict allowed extensions and MIME types.
  - Generate server-side random names only.
  - Consider storing outside the web root and serving through controlled download logic.

## Suggested Patch Sequence

1. Fix authorization and IDOR checks first because they affect broad data exposure.
2. Fix parameter tampering in wallet and trading flows because they affect state integrity.
3. Fix SQL injection next because it affects account and admin query surfaces.
4. Add CSRF protection across all mutating routes.
5. Fix stored XSS and upload handling to reduce client-side and content risks.

## Comparison Guidance

When building the patched version later:

- Keep route names and overall page flow stable where possible.
- Prefer small, isolated commits grouped by vulnerability family.
- Do not remove this file; use it as the mapping layer between vulnerable and patched branches.
