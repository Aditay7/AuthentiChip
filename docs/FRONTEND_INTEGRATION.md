# Frontend Integration Guide - Role-Based Dashboard Routing

## 🎯 Overview

Your backend now returns the user's **role** in the login response, enabling your frontend to immediately redirect users to the appropriate dashboard without additional API calls.

---

## 📡 Updated API Response

### Login Endpoint: `POST /api/v1/auth/login`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "66519f...",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "admin",           // ← Use this for routing!
    "organization": "Factory A"
  }
}
```

---

## 🚀 Frontend Implementation Steps

### 1. **Handle Login Response**

After successful login, extract the `role` from the response:

```javascript
// Example pseudo-code
const response = await fetch('/api/v1/auth/login', {
  method: 'POST',
  body: JSON.stringify({ email, password })
});

const data = await response.json();

// Store token
localStorage.setItem('access_token', data.access_token);

// Store user info (optional but recommended)
localStorage.setItem('user', JSON.stringify(data.user));

// Route based on role
if (data.user.role === 'admin') {
  // Redirect to admin dashboard
  window.location.href = '/admin/dashboard';
} else if (data.user.role === 'worker') {
  // Redirect to worker dashboard
  window.location.href = '/worker/dashboard';
}
```

---

### 2. **Protect Routes on Page Refresh**

When the user refreshes the page or visits directly, verify their role:

```javascript
// On app initialization or route guard
const token = localStorage.getItem('access_token');

if (token) {
  // Option A: Use stored user data (faster)
  const user = JSON.parse(localStorage.getItem('user'));
  redirectBasedOnRole(user.role);
  
  // Option B: Verify with backend (more secure)
  const response = await fetch('/api/v1/auth/me', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const userData = await response.json();
  redirectBasedOnRole(userData.role);
}
```

---

### 3. **Route Protection Logic**

Implement route guards to prevent unauthorized access:

```javascript
// Pseudo-code for route protection
function protectRoute(requiredRole) {
  const user = JSON.parse(localStorage.getItem('user'));
  
  if (!user) {
    // Not logged in
    redirectToLogin();
    return false;
  }
  
  if (requiredRole && user.role !== requiredRole) {
    // Wrong role - redirect to their dashboard
    if (user.role === 'admin') {
      window.location.href = '/admin/dashboard';
    } else {
      window.location.href = '/worker/dashboard';
    }
    return false;
  }
  
  return true;
}

// Usage:
// On admin pages: protectRoute('admin')
// On worker pages: protectRoute('worker')
```

---

## 🔐 Security Recommendations

### 1. **Always Verify Token on Backend**
- Frontend role checks are for UX only
- Backend must verify the JWT token on every protected endpoint
- Never trust client-side role data for authorization

### 2. **Token Storage**
- Store `access_token` in `localStorage` or `sessionStorage`
- Consider using `httpOnly` cookies for better security (requires backend changes)

### 3. **Token Expiration Handling**
- Your tokens expire after 15 minutes (configurable)
- Implement token refresh logic or redirect to login on 401 errors

---

## 📋 Complete Flow Diagram

```
User Login
    ↓
POST /auth/login
    ↓
Backend validates credentials
    ↓
Returns: { access_token, user: { role, ... } }
    ↓
Frontend stores token & user data
    ↓
Check user.role
    ↓
    ├─→ role === "admin"  → Redirect to /admin/dashboard
    └─→ role === "worker" → Redirect to /worker/dashboard

On Page Refresh/Direct Access
    ↓
Check localStorage for token
    ↓
    ├─→ No token → Redirect to /login
    └─→ Has token
            ↓
        Get user.role from localStorage
        OR
        Call GET /auth/me to verify
            ↓
        Redirect to appropriate dashboard
```

---

## 🧪 Testing the Changes

### Test Case 1: Admin Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123"
  }'
```

**Expected Response:**
```json
{
  "access_token": "...",
  "token_type": "bearer",
  "user": {
    "role": "admin",
    ...
  }
}
```

### Test Case 2: Worker Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "worker@example.com",
    "password": "worker123"
  }'
```

**Expected Response:**
```json
{
  "access_token": "...",
  "token_type": "bearer",
  "user": {
    "role": "worker",
    ...
  }
}
```

### Test Case 3: Verify Token
```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected Response:**
```json
{
  "id": "...",
  "email": "user@example.com",
  "name": "...",
  "role": "admin",  // or "worker"
  "contact": "...",
  "organization": "...",
  "last_active": "..."
}
```

---

## ✅ What Changed in Backend

1. **`/auth/login` endpoint** now returns:
   - ✅ `access_token` (same as before)
   - ✅ `token_type` (same as before)
   - ✨ **NEW:** `user` object with `role`, `id`, `email`, `name`, `organization`

2. **`/auth/me` endpoint** now returns complete user info:
   - ✅ All user fields including `role`
   - Use this to verify token and get fresh user data

---

## 🎨 Frontend Routing Examples

### React Router Example
```jsx
// Protect admin routes
<Route 
  path="/admin/*" 
  element={
    <ProtectedRoute requiredRole="admin">
      <AdminDashboard />
    </ProtectedRoute>
  } 
/>

// Protect worker routes
<Route 
  path="/worker/*" 
  element={
    <ProtectedRoute requiredRole="worker">
      <WorkerDashboard />
    </ProtectedRoute>
  } 
/>
```

### Vue Router Example
```javascript
router.beforeEach((to, from, next) => {
  const user = JSON.parse(localStorage.getItem('user'));
  
  if (to.meta.requiresAuth && !user) {
    next('/login');
  } else if (to.meta.role && user.role !== to.meta.role) {
    // Redirect to their dashboard
    next(user.role === 'admin' ? '/admin/dashboard' : '/worker/dashboard');
  } else {
    next();
  }
});
```

### Vanilla JavaScript Example
```javascript
// On login page
async function handleLogin(email, password) {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('user', JSON.stringify(data.user));
  
  // Redirect based on role
  window.location.href = data.user.role === 'admin' 
    ? '/admin-dashboard.html' 
    : '/worker-dashboard.html';
}
```

---

## 🔄 Logout Implementation

```javascript
function logout() {
  // Clear stored data
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  
  // Redirect to login
  window.location.href = '/login';
}
```

---

## 📝 Summary

**What you need to do in your frontend:**

1. ✅ After successful login, read `response.user.role`
2. ✅ Redirect to `/admin/dashboard` if role is `"admin"`
3. ✅ Redirect to `/worker/dashboard` if role is `"worker"`
4. ✅ Store the token and user info in localStorage
5. ✅ On page refresh, check the stored role and redirect accordingly
6. ✅ Optionally call `/auth/me` to verify the token is still valid

**What the backend now provides:**

1. ✅ User role in login response
2. ✅ Complete user info in `/auth/me` endpoint
3. ✅ JWT token for authentication

You're all set! The backend changes are complete. Just implement the frontend routing logic based on the `role` field.
