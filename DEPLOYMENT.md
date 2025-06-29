# Deployment Guide

## Backend URL Configuration

The frontend now uses environment variables to configure the backend URL, making it easy to deploy to different environments.

### Local Development

For local development, the app will automatically use `http://localhost:8000` as the default backend URL.

### Production Deployment

When deploying to production (Vercel, Netlify, etc.), you need to set the `NEXT_PUBLIC_BACKEND_URL` environment variable to point to your Railway backend.

## Environment Variables

### Frontend (Vercel/Netlify)

Set this environment variable in your frontend deployment:

```
NEXT_PUBLIC_BACKEND_URL=https://your-railway-app.railway.app
```

### Backend (Railway)

Set this environment variable in your Railway deployment:

```
GOOGLE_API_KEY=your_google_api_key_here
```

## Deployment Steps

### 1. Deploy Backend to Railway

1. Push your code to GitHub
2. Connect your repository to Railway
3. Railway will automatically detect the Python app
4. Add the `GOOGLE_API_KEY` environment variable in Railway dashboard
5. Deploy and get your Railway URL (e.g., `https://your-app.railway.app`)

### 2. Deploy Frontend to Vercel

1. Push your code to GitHub
2. Connect your repository to Vercel
3. Add environment variable:
   - **Name**: `NEXT_PUBLIC_BACKEND_URL`
   - **Value**: `https://your-railway-app.railway.app`
4. Deploy

### 3. Test the Connection

1. Visit your Vercel frontend URL
2. Try sending a message
3. Check that it connects to your Railway backend

## Configuration Files

- `src/config.ts` - Central configuration management
- `backend/railway.toml` - Railway deployment configuration
- `backend/railway.json` - Alternative Railway configuration
- `backend/Procfile` - Railway native Python deployment

## Troubleshooting

### Frontend can't connect to backend

1. Check that `NEXT_PUBLIC_BACKEND_URL` is set correctly
2. Verify the Railway backend is running
3. Test the backend URL directly: `https://your-app.railway.app/api/health`

### Backend not starting

1. Check Railway logs for errors
2. Verify `GOOGLE_API_KEY` is set in Railway
3. Check that all dependencies are installed correctly

### CORS Issues

The backend is configured to allow requests from:
- `http://localhost:3000` (local development)
- `https://*.railway.app` (Railway)
- `https://*.vercel.app` (Vercel)
- `https://*.netlify.app` (Netlify) 