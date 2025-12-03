# API Testing Guide

Base URL: `http://localhost:8000/api/v1`

## Auth

### Signup
- **POST** `/auth/signup`
- **Body**
```json
{
  "email": "worker@example.com",
  "password": "securepassword",
  "name": "Worker One",
  "role": "worker",
  "contact": "+1-555-0100",
  "organization": "Factory A"
}
```
- **Notes**
  - Self-service signup only supports the `worker` role. Admins must be created by an existing admin via the admin APIs.
  - Returns the created user (id, email, role, metadata).

### Login
- **POST** `/auth/login`
- **Body**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```
- **Response**
```json
{
  "access_token": "jwt_token_string",
  "token_type": "bearer",
  "user": {
    "id": "66519f...",
    "email": "user@example.com",
    "name": "Worker One",
    "role": "worker",
    "organization": "Factory A"
  }
}
```
- **Notes**
  - The `role` field in the response is critical for frontend routing
  - Use `role` to redirect to the appropriate dashboard:
    - `"admin"` → Admin Dashboard
    - `"worker"` → Worker Dashboard

### Me (Protected)
- **GET** `/auth/me`
- **Header**
```
Authorization: Bearer <access_token>
```
- **Sample response**
```json
{
  "id": "66519f...",
  "email": "user@example.com",
  "name": "Worker One",
  "role": "worker",
  "contact": "+1-555-0100",
  "organization": "Factory A",
  "last_active": "2025-05-20T10:01:42.000000+00:00"
}
```

## Admin Management (Admin role only)

### Create worker/admin
- **POST** `/admins`
- **Headers** `Authorization: Bearer <admin_token>`
- **Body**
```json
{
  "email": "worker1@example.com",
  "password": "strong-pass",
  "name": "Worker One",
  "role": "worker",
  "contact": "+1-555-0100",
  "organization": "Factory A"
}
```
- **Response** `201 Created` → `AdminOut` object.

### List users
- **GET** `/admins`
- **Query params** `role` (optional), `include_inactive=false`
- Returns only users in the admin’s organization.

### Update user
- **PATCH** `/admins/{user_id}`
- Body supports partial fields (`name`, `role`, `contact`, `organization`, `password`, `is_active`).

### Deactivate user
- **DELETE** `/admins/{user_id}`
- Soft-deletes (sets `is_active=false`). User cannot log in afterward.

---

## IC Library (Ground Truth Database)

The IC Library APIs allow you to create and manage "ground truth" IC records that scans will be compared against.

### Create IC Record
- **POST** `/ic`
- **Body**
```json
{
  "manufacturer": "Texas Instruments",
  "base_part_number": "SN74HC595",
  "package_type": "DIP",
  "pin_count": 16,
  "full_part_numbers": ["SN74HC595N", "SN74HC595NE4"],
  "allowed_markings": ["74HC595", "SN74HC595"],
  "package_dimensions": {
    "length_min_mm": 19.0,
    "length_nom_mm": 19.5,
    "length_max_mm": 20.0,
    "breadth_min_mm": 6.0,
    "breadth_nom_mm": 6.5,
    "breadth_max_mm": 7.0
  },
  "confidence_score": 0,
  "datecode_pattern": "^\\d{4}$"
}
```
- **Response** `201 Created`
```json
{
  "id": "693029aefff628097ed0fcf0",
  "manufacturer": "Texas Instruments",
  "base_part_number": "SN74HC595",
  "package_type": "DIP",
  "pin_count": 16,
  "full_part_numbers": ["SN74HC595N", "SN74HC595NE4"],
  "allowed_markings": ["74HC595", "SN74HC595"],
  "package_dimensions": {
    "length_min_mm": 19.0,
    "length_nom_mm": 19.5,
    "length_max_mm": 20.0,
    "breadth_min_mm": 6.0,
    "breadth_nom_mm": 6.5,
    "breadth_max_mm": 7.0
  },
  "model_1": {"passed": false, "score": null},
  "model_2": {"passed": false, "score": null},
  "model_3": {"passed": false, "score": null},
  "model_4": {"passed": false, "score": null},
  "confidence_score": 0,
  "datecode_pattern": "^\\d{4}$"
}
```
- **Notes**
  - Only `manufacturer`, `base_part_number`, and `package_type` are required
  - All other fields are optional
  - `model_1` through `model_4` default to `{"passed": false, "score": null}`

### List IC Records
- **GET** `/ic`
- **Query Parameters**
  - `manufacturer` (optional) - Filter by manufacturer name
  - `base_part_number` (optional) - Filter by base part number
  - `skip` (optional, default: 0) - Number of records to skip for pagination
  - `limit` (optional, default: 50, max: 100) - Number of records to return
- **Example Requests**
  - List all: `GET /ic`
  - Filter by manufacturer: `GET /ic?manufacturer=Texas%20Instruments`
  - Filter by part number: `GET /ic?base_part_number=SN74HC595`
  - Pagination: `GET /ic?skip=10&limit=20`
- **Response** `200 OK` - Array of IC records

### Get Single IC Record
- **GET** `/ic/{id}`
- **Path Parameters**
  - `id` - MongoDB ObjectId of the IC record
- **Response** `200 OK` - Single IC record
- **Error** `404 Not Found` if ID doesn't exist or is invalid

### Update IC Record
- **PATCH** `/ic/{id}`
- **Path Parameters**
  - `id` - MongoDB ObjectId of the IC record
- **Body** (all fields optional for partial update)
```json
{
  "pin_count": 20,
  "confidence_score": 95,
  "allowed_markings": ["74HC595", "SN74HC595", "HC595"]
}
```
- **Response** `200 OK` - Updated IC record
- **Error** `404 Not Found` if ID doesn't exist
- **Notes**
  - Only include fields you want to update
  - Fields with `null` values are ignored (won't overwrite existing data)

### Delete IC Record
- **DELETE** `/ic/{id}`
- **Path Parameters**
  - `id` - MongoDB ObjectId of the IC record
- **Response** `200 OK`
```json
{
  "message": "IC record 693029aefff628097ed0fcf1 deleted successfully"
}
```
- **Error** `404 Not Found` if ID doesn't exist
- **Notes**
  - This is a hard delete (permanent removal from database)

---

## Authentication Status

- **Auth endpoints** (`/auth/*`): ✅ Implemented with JWT authentication
- **Admin endpoints** (`/admins/*`): ✅ Implemented (requires admin role)
- **IC Library endpoints** (`/ic/*`): ⚠️ **No authentication required** (as per current implementation)
