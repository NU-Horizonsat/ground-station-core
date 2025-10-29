# Web UI Features - Quick Reference

## 🎉 What's New in the Web UI

Your Streamlit web interface now includes extensive features for satellite operations:

### Fixed Issues ✅
- ✓ Position calculation error fixed (velocity attribute issue)
- ✓ Real-time tracking now works with auto-refresh
- ✓ Enhanced world map with more details

### New Features Added 🚀

#### 🗺️ Enhanced Satellite Tracking Tab

**Interactive World Map:**
- ✅ Adjustable ground track length (30-200 minutes)
- ✅ Optional visibility footprint circle
- ✅ Hover tooltips with detailed info
- ✅ Emoji markers (📡 satellite, 🏠 local GS, ☁️ AWS GS)
- ✅ Real-time position updates
- ✅ Orbit statistics display

**Real-time Tracking:**
- ✅ Auto-update checkbox for 5-second refresh
- ✅ Manual update button
- ✅ Separate ground track update button
- ✅ Timestamp on last update
- ✅ Continuous tracking when enabled

**Position Display:**
- ✅ All orbital parameters
- ✅ Visibility status (🟢/🔴)
- ✅ Real-time velocity
- ✅ Range to ground station

#### 🎛️ New Advanced Tab

**Rotator Control:**
- ✅ Manual antenna pointing (Az/El sliders)
- ✅ Auto-track satellite button
- ✅ Real-time position display
- ✅ One-click pointing

**TLE Management:**
- ✅ Fetch from Celestrak/Space-Track
- ✅ Upload TLE files
- ✅ Custom URL support

**Frequency & Doppler:**
- ✅ Carrier frequency input
- ✅ Real-time Doppler shift calculation
- ✅ Corrected frequency display
- ✅ Radio control integration

**Data Export:**
- ✅ Download session logs
- ✅ Export ground track data
- ✅ Save configuration as JSON
- ✅ One-click downloads

**System Information:**
- ✅ Library status indicators
- ✅ Session statistics
- ✅ Current satellite info
- ✅ Activity counter

## 🎯 How to Use New Features

### Real-time Satellite Tracking

```
1. Go to "Satellite Tracking" tab
2. Select satellite (e.g., ISS)
3. Click "Load Satellite"
4. Check "🔄 Real-time Tracking"
5. Watch position update every 5 seconds
```

**The page will automatically refresh!** 🔄

### Custom Ground Track

```
1. After loading satellite
2. Use slider: "Ground Track Length" (30-200 min)
3. Toggle "Show Footprint" for visibility circle
4. Map updates with new settings
```

### Rotator Auto-Track

```
1. Go to "Advanced" tab
2. Ensure satellite loaded and position updated
3. Click "🔄 Track Satellite"
4. Antenna points to satellite automatically
```

### Doppler Compensation

```
1. Advanced tab → Frequency & Doppler section
2. Enter carrier frequency (MHz)
3. Update satellite position
4. See real-time doppler shift
5. Use corrected frequency for radio
```

### Export Data

```
Advanced Tab → Data Export:
- 📊 Export Session Log (all activities)
- 🗺️ Export Ground Track (CSV/JSON)
- ⚙️ Export Configuration (settings backup)
```

## 🎨 UI Improvements

### Better Visualizations
- **World Map**: Natural Earth projection with countries
- **Hover Info**: Rich tooltips on all map elements
- **Color Coding**: Blue track, red satellite, green GS
- **Icons**: Emoji markers for better visibility

### User Experience
- **Responsive**: Works on all screen sizes
- **Auto-refresh**: Set and forget tracking
- **Help Text**: Inline instructions
- **Error Messages**: Clear, actionable feedback

### Performance
- **Optimized**: Smooth map rendering
- **Configurable**: Adjust track length for performance
- **Efficient**: Only updates when needed

## 📊 Comparison: Desktop vs Web UI

| Feature | Desktop UI | Web UI |
|---------|-----------|--------|
| World Map | Cartopy (static) | Plotly (interactive) |
| Real-time Track | Manual refresh | Auto-refresh ✅ |
| Rotator Control | ❌ | ✅ Manual + Auto |
| Doppler Calc | ❌ | ✅ Real-time |
| Data Export | Limited | ✅ Full suite |
| TLE Upload | File dialog | ✅ Drag & drop |
| Mobile Access | ❌ | ✅ Responsive |
| Hover Info | ❌ | ✅ Rich tooltips |
| Session Logs | Terminal only | ✅ Exportable |

## 🔥 Pro Tips

### Tip 1: Continuous Monitoring
```
1. Enable "Real-time Tracking" on Sat Tracking tab
2. Leave browser tab open
3. Position updates every 5 seconds automatically
4. Map redraws with new position
```

### Tip 2: Multi-Device Monitoring
```
- Start web UI on main computer
- Access from phone: http://<ip>:8501
- Monitor satellite on mobile while outdoors
- Control rotator remotely
```

### Tip 3: Pre-Pass Preparation
```
1. Load satellite 30 min before pass
2. Go to Pass Prediction tab
3. Calculate passes for next 24 hours
4. Note AOS/LOS times
5. Set up rotator auto-track
6. Enable real-time tracking at AOS
```

### Tip 4: Doppler Tracking
```
1. Advanced tab → Enter downlink frequency
2. Start real-time tracking
3. Watch doppler shift update
4. Use corrected frequency for reception
5. Manually tune or auto-correct
```

### Tip 5: Session Documentation
```
- All activities logged automatically
- Export log at end of session
- Includes timestamps and actions
- Great for operations records
```

## 🚀 Quick Start Commands

### Launch Web UI
```powershell
# Windows
.\start_web.ps1

# Linux/macOS
./start_web.sh

# Manual
streamlit run streamlit_ui.py
```

### Full Stack
```powershell
# Terminal 1: API
python backend/api_server.py

# Terminal 2: Web UI
streamlit run streamlit_ui.py

# Terminal 3: Desktop UI (optional)
python ui_v2.py
```

## 📱 Mobile Access

```bash
# Find your computer's IP
ipconfig  # Windows
ifconfig  # Linux/macOS

# Start web UI with network access
streamlit run streamlit_ui.py --server.address 0.0.0.0

# Access from mobile
http://192.168.1.XXX:8501
```

## 🐛 Troubleshooting

### Real-time tracking not working
- **Check:** Is checkbox enabled?
- **Fix:** Disable and re-enable checkbox
- **Note:** Browser tab must stay open

### Map not updating
- **Click:** "🗺️ Update Ground Track" button
- **Or:** Adjust track length slider
- **Or:** Reload page (Ctrl+R)

### Position shows old data
- **Click:** "🎯 Update Position Now"
- **Check:** Satellite is loaded
- **Verify:** Skyfield installed

### Doppler not calculating
- **Check:** Satellite position updated
- **Verify:** Velocity data available
- **Try:** Re-load satellite TLE

## 🎓 Advanced Workflows

### Automated Pass Tracking
```
1. Load satellite
2. Go to Pass Prediction
3. Calculate next passes
4. Note AOS time
5. At AOS-5min: Enable real-time tracking
6. Advanced tab: Enable rotator auto-track
7. Monitor until LOS
8. Export session log
```

### Multi-Satellite Monitoring
```
1. Browser Tab 1: ISS tracking
2. Browser Tab 2: NOAA satellite
3. Browser Tab 3: CubeSat
4. Each with independent real-time tracking
5. Switch tabs as needed
```

### Remote Operations
```
1. Server: Start web UI with --server.address 0.0.0.0
2. Desktop: Full monitoring and control
3. Tablet: Quick status checks
4. Phone: Emergency control
```

## 📚 Next Steps

1. **Try Real-time Tracking**: Enable and watch it work!
2. **Explore Advanced Tab**: Rotator control, doppler, exports
3. **Test on Mobile**: See responsive design
4. **Export Your Data**: Try all export features
5. **Read Full Guide**: See [WEB_UI_GUIDE.md](WEB_UI_GUIDE.md)

## 🎉 Summary

The web UI now has:
- ✅ Real-time auto-refresh tracking (5s updates)
- ✅ Interactive world map with footprint
- ✅ Rotator control (manual + auto-track)
- ✅ Real-time Doppler calculation
- ✅ Complete data export suite
- ✅ TLE management and updates
- ✅ Session logging and statistics
- ✅ Mobile-responsive design
- ✅ Rich hover tooltips
- ✅ Professional-grade features

**It's now a complete satellite ground station interface! 🛰️**

Enjoy your enhanced web UI! 🚀
