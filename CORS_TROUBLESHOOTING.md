# CORS Troubleshooting Guide

## CORS Error Solutions

### ✅ **Fixed: Updated Backend CORS Configuration**

The backend now allows all origins (`allow_origins=["*"]`) which should resolve CORS issues.

### 🔍 **Debugging Steps**

1. **Test CORS Configuration:**
   ```
   https://your-railway-app.railway.app/api/cors-test
   ```
   This will show you the exact origin header being sent.

2. **Check Browser Console:**
   - Open browser dev tools (F12)
   - Look for CORS error messages
   - Note the exact error details

3. **Verify Environment Variables:**
   - Frontend: `NEXT_PUBLIC_BACKEND_URL` is set correctly
   - Backend: `GOOGLE_API_KEY` is set in Railway

### 🚨 **Common CORS Issues & Solutions**

#### **Issue: "Access to fetch at '...' from origin '...' has been blocked by CORS policy"**

**Solution:** ✅ Already fixed - backend now allows all origins

#### **Issue: "No 'Access-Control-Allow-Origin' header"**

**Solution:** ✅ Already fixed - backend now allows all origins

#### **Issue: "Request header field content-type is not allowed"**

**Solution:** ✅ Already fixed - backend allows all headers

### 🔧 **Manual CORS Test**

1. **Open browser console** on your Vercel frontend
2. **Run this test:**
   ```javascript
   fetch('https://your-railway-app.railway.app/api/cors-test')
     .then(response => response.json())
     .then(data => console.log('CORS Test:', data))
     .catch(error => console.error('CORS Error:', error));
   ```

3. **Expected result:** Should return JSON with origin information
4. **If error:** Check the exact error message

### 📋 **Deployment Checklist**

- [ ] Backend deployed to Railway ✅
- [ ] Frontend deployed to Vercel ✅
- [ ] `NEXT_PUBLIC_BACKEND_URL` set in Vercel ✅
- [ ] `GOOGLE_API_KEY` set in Railway ✅
- [ ] CORS configuration updated ✅
- [ ] App redeployed after changes ✅

### 🎯 **Next Steps**

1. **Redeploy backend** to Railway with updated CORS config
2. **Test the connection** using the CORS test endpoint
3. **Try sending a message** from your Vercel frontend

The CORS issue should now be resolved! 🎉 