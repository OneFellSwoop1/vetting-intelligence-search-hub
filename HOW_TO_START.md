# 🚀 How to Start the POISSON AI® Application

## Quick Start (For You)

The fastest way to start your application:

```bash
# Navigate to project root
cd /Users/nicholas/Projects/vetting-intelligence-search-hub

# Run the automated start script
./start_application.sh
```

---

## Manual Start (Step by Step)

If you prefer to start services manually or the script doesn't work:

### 1️⃣ **Start the Backend API**

```bash
# Open Terminal 1
cd /Users/nicholas/Projects/vetting-intelligence-search-hub/backend

# Activate virtual environment
source ../venv/bin/activate

# Start the backend server
python start_server.py
```

**Expected output:**
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:app.main:🚀 Starting Vetting Intelligence Search Hub API...
INFO:app.database:✅ Database connected and initialized
INFO:app.main:✅ Redis cache connected successfully
INFO:app.main:🎯 API startup completed successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Backend will be available at:** `http://127.0.0.1:8000`

---

### 2️⃣ **Start the Frontend**

```bash
# Open Terminal 2 (new terminal window/tab)
cd /Users/nicholas/Projects/vetting-intelligence-search-hub/frontend

# Start Next.js development server
npm run dev
```

**Expected output:**
```
▲ Next.js 14.2.29
- Local:        http://localhost:3000

✓ Starting...
✓ Ready in 1132ms
```

**Frontend will be available at:** `http://localhost:3000`

---

## 🌐 Access Your Application

Once both services are running:

### **Landing Page** (New!)
**URL:** http://localhost:3000/
- Professional marketing page
- "DEMO NOW" button to enter app
- Features, use cases, and information

### **Application** (Search Platform)
**URL:** http://localhost:3000/app
- Full search functionality
- Analytics and visualizations
- Multi-source data search

### **Backend API**
**URL:** http://127.0.0.1:8000
- API endpoints for data
- Automatic documentation at `/docs`

---

## 🛑 How to Stop the Application

### **Option 1: Stop All at Once**
```bash
cd /Users/nicholas/Projects/vetting-intelligence-search-hub
./stop_application.sh
```

### **Option 2: Stop Manually**
```bash
# Stop backend and frontend
pkill -f "uvicorn"
pkill -f "next dev"
```

### **Option 3: Stop from Terminal**
If running in terminal windows (not background):
- Press `Ctrl + C` in each terminal window

---

## 🔧 Troubleshooting

### **Port Already in Use**

If you see errors about ports 3000 or 8000 being in use:

```bash
# Check what's using the ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend

# Kill processes on those ports
kill -9 $(lsof -t -i:3000)  # Frontend
kill -9 $(lsof -t -i:8000)  # Backend
```

### **Backend Won't Start**

```bash
# Check if virtual environment is activated
source /Users/nicholas/Projects/vetting-intelligence-search-hub/venv/bin/activate

# Check if required packages are installed
pip list | grep fastapi

# Reinstall if needed
pip install -r requirements.txt
```

### **Frontend Won't Start**

```bash
# Make sure you're in the frontend directory
cd /Users/nicholas/Projects/vetting-intelligence-search-hub/frontend

# Check if node_modules exist
ls node_modules/

# Reinstall if needed
npm install
```

### **Can't See Recent Logs**

```bash
# Backend logs
tail -f /Users/nicholas/Projects/vetting-intelligence-search-hub/backend_restart.log

# Frontend logs  
tail -f /Users/nicholas/Projects/vetting-intelligence-search-hub/frontend.log
```

---

## 📁 Important Directories

```
vetting-intelligence-search-hub/
├── backend/              # Python FastAPI backend
│   ├── start_server.py   # Backend startup script
│   ├── app/              # Application code
│   └── environment.env   # Configuration
├── frontend/             # Next.js frontend
│   ├── package.json      # Node dependencies
│   └── src/app/          # Application pages
│       ├── page.tsx      # Landing page (/)
│       └── app/page.tsx  # Search app (/app)
├── venv/                 # Python virtual environment
├── start_application.sh  # Start everything
└── stop_application.sh   # Stop everything
```

---

## 🔑 Environment Variables

Your backend uses configuration from:
```
backend/environment.env
```

Important settings:
- Database location
- API keys (if any)
- CORS settings
- Cache configuration

**Don't commit this file to Git!** (It's already in .gitignore)

---

## 📊 Quick Health Check

After starting, verify everything is working:

```bash
# Check backend health
curl http://127.0.0.1:8000/docs

# Check frontend
curl -I http://localhost:3000

# Check if both are running
ps aux | grep -E "uvicorn|next" | grep -v grep
```

---

## 🎯 Development Workflow

### **Normal Development Session:**

1. **Morning startup:**
   ```bash
   cd /Users/nicholas/Projects/vetting-intelligence-search-hub
   ./start_application.sh
   ```

2. **Work on your code:**
   - Backend changes: Edit files in `backend/app/`
   - Frontend changes: Edit files in `frontend/src/`
   - Both will auto-reload on changes

3. **Test your changes:**
   - Visit http://localhost:3000/ for landing page
   - Visit http://localhost:3000/app for application

4. **End of day:**
   ```bash
   ./stop_application.sh
   ```

### **Making Changes:**

**Frontend changes:**
- Edit files in `frontend/src/`
- Next.js will auto-reload the page
- No need to restart the server

**Backend changes:**
- Edit files in `backend/app/`
- Uvicorn will auto-reload
- Watch the terminal for any errors

---

## 🐛 Common Issues & Solutions

### **Issue: "Module not found" errors**
**Solution:**
```bash
# Backend
cd backend
source ../venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### **Issue: "Database locked" errors**
**Solution:**
```bash
# Stop all services
./stop_application.sh

# Wait a moment
sleep 2

# Start again
./start_application.sh
```

### **Issue: Changes not showing up**
**Solution:**
```bash
# Frontend: Hard refresh browser
# Mac: Cmd + Shift + R
# Windows/Linux: Ctrl + Shift + R

# Backend: Check terminal for auto-reload confirmation
```

### **Issue: "Port 3000 already in use"**
**Solution:**
```bash
# Find and kill the process
lsof -ti:3000 | xargs kill -9

# Or use a different port
cd frontend
PORT=3001 npm run dev
```

---

## 🚀 Production Deployment

For production deployment (not development):

### **Backend:**
```bash
cd backend
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### **Frontend:**
```bash
cd frontend
npm run build
npm start
```

**Note:** See `OFFICE_DEPLOYMENT.md` for full production deployment instructions.

---

## 📝 Log Files

Your application creates these log files:

```bash
backend_restart.log     # Backend API logs
frontend.log            # Frontend Next.js logs
backend.log             # Alternative backend log location
```

**View logs in real-time:**
```bash
# Backend
tail -f backend_restart.log

# Frontend
tail -f frontend.log

# Both in split view
tmux new-session \; \
  split-window -h \; \
  send-keys 'tail -f backend_restart.log' C-m \; \
  split-window -v \; \
  send-keys 'tail -f frontend.log' C-m
```

---

## 🎓 Learning Resources

### **Backend (FastAPI):**
- Official Docs: https://fastapi.tiangolo.com/
- Your API Docs: http://127.0.0.1:8000/docs (when running)

### **Frontend (Next.js):**
- Official Docs: https://nextjs.org/docs
- React Docs: https://react.dev/

### **Your Project:**
- `README.md` - Project overview
- `ARCHITECTURE.md` - Technical architecture
- `LANDING_PAGE_IMPLEMENTATION.md` - Landing page docs
- `LOGO_INTEGRATION_SUMMARY.md` - Logo usage guide

---

## ✅ Startup Checklist

Before starting development:

- [ ] Navigate to project directory
- [ ] Virtual environment activated (backend)
- [ ] Node modules installed (frontend)
- [ ] Ports 3000 and 8000 are available
- [ ] `environment.env` file exists in backend/

**Then run:**
```bash
./start_application.sh
```

**Verify:**
- [ ] Backend responds at http://127.0.0.1:8000
- [ ] Frontend loads at http://localhost:3000
- [ ] Landing page displays correctly
- [ ] App at /app works correctly
- [ ] Search functionality works

---

## 🎉 You're All Set!

### **Quick Command Reference:**

```bash
# Start everything
./start_application.sh

# Stop everything  
./stop_application.sh

# View backend logs
tail -f backend_restart.log

# View frontend logs
tail -f frontend.log

# Check what's running
ps aux | grep -E "uvicorn|next" | grep -v grep
```

### **URLs to Remember:**

- **Landing Page:** http://localhost:3000/
- **Application:** http://localhost:3000/app
- **API Docs:** http://127.0.0.1:8000/docs

---

**Need Help?** Check the troubleshooting section above or review the documentation files in the project root.

**Happy Coding!** 🚀

