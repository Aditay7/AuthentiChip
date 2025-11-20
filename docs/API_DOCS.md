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
  "token_type": "bearer"
}
```

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
