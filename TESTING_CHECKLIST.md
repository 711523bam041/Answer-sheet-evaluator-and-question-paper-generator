# ✅ TESTING CHECKLIST

## Pre-Test Setup
- [ ] Backend and Frontend are running
- [ ] Docker-compose shows all services as "healthy"
- [ ] Can access `http://localhost:3000` in browser
- [ ] Can curl `http://localhost:5000/api/health` successfully

## Test 1: Authentication System

### Register New User
- [ ] Navigate to `/register`
- [ ] Fill in username and password
- [ ] Passwords match validation works
- [ ] Successful registration redirects to login
- [ ] Error for duplicate username
- [ ] Error for weak password (<6 chars)

### Login
- [ ] Can login with correct credentials
- [ ] Invalid credentials show error
- [ ] Token is stored in localStorage
- [ ] Redirects to `/` (Dashboard) after login
- [ ] Logout clears token and redirects to login

## Test 2: File Upload & Student Names

### Dashboard Upload Form
- [ ] Answer Key upload works
- [ ] Multiple student answer files can be selected
- [ ] Student name input fields appear after file selection
- [ ] Can edit student names
- [ ] Can remove individual student files
- [ ] Clear button resets all selections
- [ ] Submit disabled when no files selected
- [ ] Submit disabled when student name is empty

### Upload Validation
- [ ] ❌ Rejects files >50MB
- [ ] ❌ Rejects unsupported file types (.exe, .zip, etc.)
- [ ] ❌ Rejects empty files
- [ ] ✅ Accepts PDF files
- [ ] ✅ Accepts image files (jpg, png)
- [ ] ✅ Accepts text files (.txt)
- [ ] Progress bar updates during upload
- [ ] Cannot submit while upload in progress

## Test 3: Evaluation & Results

### First Evaluation
- [ ] Evaluation completes successfully
- [ ] Redirects to Results page
- [ ] Toast shows success message
- [ ] Results table displays data
- [ ] Student names appear in table (NOT just filenames)
- [ ] Scores are calculated (0-100)
- [ ] Similarity percentages are shown
- [ ] Feedback messages appear
- [ ] Timestamps are displayed

### Score Calculation
- [ ] Similar answers get high score (80-100)
- [ ] Partially similar get medium score (60-80)
- [ ] Different answers get low score (0-60)
- [ ] Blank answers get 0 score
- [ ] Progress bars show correct color:
  - [ ] Green for ≥80
  - [ ] Yellow for 60-79
  - [ ] Red for <60

## Test 4: Data Preservation (CRITICAL FIX)

### Second Evaluation - Data Should NOT Be Deleted
- [ ] Create first evaluation with 2 students (Alice, Bob)
- [ ] Note the results in the table
- [ ] Go back to Dashboard
- [ ] Create second evaluation with 2 different students (Charlie, Diana)
- [ ] Go to Results
- [ ] ✅ **All 4 students should be visible** (Alice, Bob, Charlie, Diana)
- [ ] ❌ If only Charlie & Diana visible = BUG NOT FIXED

### Batch Management
- [ ] Results are grouped by batch_id
- [ ] Each evaluation has unique batch_id
- [ ] Can filter by batch_id (if implemented)
- [ ] Historical results are preserved indefinitely

## Test 5: Results Table Features

### Sorting
- [ ] Sort by Student Name A-Z
- [ ] Sort by Student Name Z-A
- [ ] Sort by Score (low to high)
- [ ] Sort by Score (high to low)
- [ ] Sort by Similarity (low to high)
- [ ] Sort by Similarity (high to low)
- [ ] Sort by Date (newest first)
- [ ] Sort by Date (oldest first)

### Filtering
- [ ] Search by student name works
- [ ] Search by filename works
- [ ] Search by feedback works
- [ ] Flagged-only filter works
- [ ] Combine filters (search + flagged)
- [ ] Clear search removes filter
- [ ] Shows "Showing X of Y results"

### Display
- [ ] Student names are prominent
- [ ] Filenames are visible (truncated if long)
- [ ] Scores have progress bars
- [ ] Color-coded status badges
- [ ] Flagged students have warning icon
- [ ] Table scrollable on mobile

## Test 6: Plagiarism Detection

### Duplicate Detection
- [ ] Upload 2 very similar answers (copy-paste)
- [ ] Both should be flagged as plagiarism
- [ ] Feedback shows "Plagiarism Detected"
- [ ] Status shows "Flagged" badge in red
- [ ] Row is highlighted in red

### Plagiarism Threshold
- [ ] 80%+ similarity = flagged
- [ ] 79% or less = not flagged
- [ ] Threshold is configurable via env var

## Test 7: Export Functions

### CSV Download
- [ ] Click CSV button
- [ ] File downloads
- [ ] Filename is `evaluation_results.csv`
- [ ] Opens in Excel/Sheets correctly
- [ ] Contains columns: Student Name, File, Score, Similarity, Feedback, Flagged
- [ ] All data is preserved
- [ ] Timestamps are included

### PDF Download
- [ ] Click PDF button
- [ ] File downloads
- [ ] Filename is `evaluation_results.pdf`
- [ ] Opens in PDF viewer
- [ ] Header shows "Evaluation Results Report"
- [ ] Timestamp is shown
- [ ] All student results are included
- [ ] Plagiarism warnings are in red
- [ ] Formatted professionally

## Test 8: Error Handling

### Invalid Token
- [ ] Modify Authorization header to invalid token
- [ ] API returns 401 with proper error message
- [ ] Frontend redirects to login

### Missing Files
- [ ] Submit form without answer key
- [ ] Error message: "Answer key and student answers required"
- [ ] Submit form without student names
- [ ] Error message: "Please enter a name for student X"

### File Size
- [ ] Upload file >50MB
- [ ] Error: "File size exceeds maximum of 50.0MB"
- [ ] Upload continues to work after error

### Database Errors
- [ ] Check logs show database errors properly
- [ ] Error messages don't expose sensitive info
- [ ] User-friendly error messages shown

## Test 9: Performance

### Load Times
- [ ] Dashboard loads in <2 seconds
- [ ] Results page loads in <3 seconds
- [ ] First evaluation takes ~30-60 seconds (model loading)
- [ ] Subsequent evaluations faster (~20-30 seconds)
- [ ] Download CSV completes in <5 seconds
- [ ] Download PDF completes in <5 seconds

### Concurrent Users
- [ ] Can have multiple browser windows open
- [ ] Each user sees only their results
- [ ] No data leakage between users

## Test 10: Logging

### Check Backend Logs
- [ ] Look in `backend/logs/app.log`
- [ ] Entries for user registration
- [ ] Entries for login attempts
- [ ] Entries for file uploads
- [ ] Entries for evaluation start/completion
- [ ] Entries for errors (no stack traces in production)
- [ ] Proper timestamps on all entries

### Log Levels
- [ ] Errors are logged at ERROR level
- [ ] Info messages at INFO level
- [ ] Warnings at WARNING level
- [ ] Rotating files when size >10MB

## Test 11: API Endpoints (Curl)

### Health Check
```bash
curl http://localhost:5000/api/health
# Should return: {"status": "ok", "message": "API is running", "database": "connected"}
```
- [ ] Returns 200 status
- [ ] Shows database is connected

### Register
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","password":"pass123"}'
```
- [ ] New user registration works
- [ ] Duplicate username rejected
- [ ] Weak password rejected

### Login
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123!"}'
```
- [ ] Returns access token
- [ ] Token can be used for auth
- [ ] Invalid credentials return 401

### Results (Protected)
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5000/api/results
```
- [ ] Returns array of results
- [ ] Includes student_name field
- [ ] Includes created_at timestamp
- [ ] Ordered by newest first

## Test 12: Security

### CORS
- [ ] Frontend can communicate with backend
- [ ] No CORS errors in browser console
- [ ] Credentials are sent in requests

### Token Expiry
- [ ] Logout clears token
- [ ] Expired token redirects to login
- [ ] Cannot access protected routes without token

### Password Security
- [ ] Passwords are hashed (not visible in logs)
- [ ] Passwords are hashed in database
- [ ] Can't retrieve password from database

### File Security
- [ ] Filenames are sanitized
- [ ] No path traversal possible
- [ ] File types are validated

## Test 13: Responsive Design

### Desktop (1920x1080)
- [ ] All elements visible
- [ ] No horizontal scrolling
- [ ] Table displays well

### Tablet (768x1024)
- [ ] Sidebar collapses to hamburger menu
- [ ] Upload form adapts
- [ ] Table is readable

### Mobile (375x667)
- [ ] All features accessible
- [ ] Touch-friendly buttons
- [ ] No overlapping elements
- [ ] Sidebar slide-in works

## Test 14: Browser Compatibility

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

Each browser should:
- [ ] Login works
- [ ] File upload works
- [ ] Results display correctly
- [ ] Download functions work
- [ ] No console errors

## Test 15: Stress Testing

### Multiple Uploads
- [ ] Upload 5+ times in succession
- [ ] All results preserved
- [ ] No duplicate results
- [ ] No missing results

### Large Batches
- [ ] Upload 10 student files at once
- [ ] All 10 evaluate correctly
- [ ] All 10 appear in results

### Many Results
- [ ] With 50+ results in table
- [ ] Sorting works smoothly
- [ ] Filtering works smoothly
- [ ] Search is responsive

## Summary

**Total Tests**: 100+

**Before Implementation**:
- ❌ Data loss on upload
- ❌ No student names
- ❌ No validation
- ❌ No logging
- ❌ Poor error handling

**After Implementation**:
- ✅ Data preserved indefinitely
- ✅ Student names captured and displayed
- ✅ Comprehensive file validation
- ✅ Structured logging system
- ✅ Proper error handling and messages

---

**Testing Complete!** ✅

If all tests pass, the system is ready for:
- [ ] Production deployment
- [ ] User testing
- [ ] Further development (Step 2+)

**If any test fails**, check:
1. Backend logs: `backend/logs/app.log`
2. Browser console: Press F12
3. Docker logs: `docker-compose logs`
