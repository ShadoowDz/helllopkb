# FBX to MDL Converter

A complete web application that converts FBX 3D models to MDL format compatible with the GoldSrc engine (Counter-Strike 1.6). This application provides a modern web interface for uploading FBX files and automatically converting them to game-ready MDL models with animations, mesh data, and full GoldSrc compatibility.

## 🌟 Features

### Core Functionality
- **FBX to MDL Conversion**: Complete pipeline from FBX to GoldSrc MDL format
- **Animation Support**: Preserves animations from FBX files
- **Mesh Processing**: Handles complex geometries and textures
- **Bone System**: Maintains rigging and skeletal animations
- **Real-time Progress**: Live progress tracking with detailed logs

### Web Interface
- **Modern UI**: Clean, responsive design with drag-and-drop support
- **Progress Tracking**: Real-time conversion progress with detailed logs
- **Error Handling**: Comprehensive error reporting and troubleshooting
- **Download Management**: Packaged results in ZIP format
- **Mobile Friendly**: Responsive design for all devices

### Security & Performance
- **File Validation**: Secure FBX file validation and sanitization
- **Rate Limiting**: Protection against abuse (5 uploads per hour per IP)
- **Sandboxing**: Isolated processing environment
- **Size Limits**: 100MB maximum file size
- **Content Security**: Malicious file detection and prevention

## 🔧 Technical Stack

- **Backend**: Python Flask with async job processing
- **3D Processing**: Blender (headless mode) with Source Tools addon
- **Compilation**: GoldSrc SDK studiomdl.exe via Wine
- **Frontend**: Modern HTML5/CSS3/JavaScript with real-time updates
- **Containerization**: Docker for easy deployment
- **File Handling**: Secure upload and validation system

## 📋 Prerequisites

### For Docker Deployment (Recommended)
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB free disk space

### For Manual Installation
- Ubuntu 20.04+ or similar Linux distribution
- Python 3.8+
- Blender 3.6+
- Wine (for studiomdl.exe)
- GoldSrc SDK with studiomdl.exe

## 🚀 Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fbx-to-mdl-converter
   ```

2. **Prepare studiomdl.exe**
   ```bash
   mkdir -p docker
   # Copy your studiomdl.exe from GoldSrc SDK to docker/studiomdl.exe
   cp /path/to/your/studiomdl.exe docker/
   ```

3. **Build and run with Docker**
   ```bash
   docker build -t fbx-to-mdl-converter .
   docker run -p 5000:5000 fbx-to-mdl-converter
   ```

4. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## 🔨 Manual Installation

### 1. System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-dev build-essential curl wget unzip
```

**Install Blender:**
```bash
wget https://mirror.clarkson.edu/blender/release/Blender3.6/blender-3.6.0-linux-x64.tar.xz
tar -xf blender-3.6.0-linux-x64.tar.xz
sudo mv blender-3.6.0-linux-x64 /opt/blender
sudo ln -s /opt/blender/blender /usr/local/bin/blender
```

**Install Wine:**
```bash
sudo dpkg --add-architecture i386
wget -nc https://dl.winehq.org/wine-builds/winehq.key
sudo apt-key add winehq.key
sudo add-apt-repository 'deb https://dl.winehq.org/wine-builds/ubuntu/ focal main'
sudo apt update
sudo apt install winehq-stable
```

### 2. Setup Wine Environment
```bash
export WINEPREFIX=$HOME/.wine
export WINEARCH=win32
wine --version
wineboot --init
```

### 3. Install GoldSrc SDK
1. Download the Half-Life SDK from Valve
2. Extract and locate `studiomdl.exe`
3. Copy to `/usr/local/wine/cstrike/studiomdl.exe`
```bash
sudo mkdir -p /usr/local/wine/cstrike
sudo cp /path/to/studiomdl.exe /usr/local/wine/cstrike/
sudo chmod +x /usr/local/wine/cstrike/studiomdl.exe
```

### 4. Install Blender Source Tools
```bash
wget https://github.com/Artfunkel/BlenderSourceTools/archive/refs/heads/master.zip
unzip master.zip
sudo cp -r BlenderSourceTools-master/io_scene_valvesource /opt/blender/3.6/scripts/addons/
```

### 5. Python Dependencies
```bash
cd backend
pip3 install -r requirements.txt
```

### 6. Run the Application
```bash
cd backend
python3 app.py
```

## 📖 Usage Guide

### 1. Upload FBX File
- Drag and drop your FBX file or click "Browse Files"
- Maximum file size: 100MB
- Supported format: .fbx files with embedded textures

### 2. Configure Options
- **Scale**: Adjust model size (0.1 - 100.0)
- **Bodygroup Name**: Set the bodygroup identifier

### 3. Start Conversion
- Click "Start Conversion"
- Monitor real-time progress
- View detailed conversion logs

### 4. Download Results
- Download ZIP package containing:
  - `.mdl` file (GoldSrc model)
  - `.qc` file (model script)
  - `.smd` files (mesh and animations)
  - `compile.log` (compilation log)
  - Original FBX file

## 🗂️ Project Structure

```
fbx-to-mdl-converter/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── fbx_processor.py       # FBX processing logic
│   ├── utils.py              # Utility functions
│   ├── requirements.txt      # Python dependencies
│   ├── static/
│   │   ├── style.css         # Frontend styles
│   │   └── script.js         # Frontend JavaScript
│   ├── uploads/              # Temporary upload directory
│   └── outputs/              # Temporary output directory
├── frontend/
│   └── index.html            # Main HTML template
├── docker/
│   └── studiomdl.exe         # GoldSrc compiler (user-provided)
├── Dockerfile                # Container configuration
└── README.md                 # This file
```

## 🔧 Configuration

### Environment Variables

- `SECRET_KEY`: Flask secret key (default: auto-generated)
- `WINEPREFIX`: Wine environment path (default: `~/.wine`)
- `BLENDER_PATH`: Blender executable path (default: `blender`)
- `STUDIOMDL_PATH`: studiomdl.exe path (default: `/usr/local/wine/cstrike/studiomdl.exe`)

### Rate Limiting

Default: 5 uploads per hour per IP address
Configure in `backend/utils.py`:
```python
rate_limiter = RateLimiter(max_requests=5, time_window=3600)
```

### File Size Limits

Default: 100MB maximum upload size
Configure in `backend/app.py`:
```python
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
```

## 🛠️ Development

### Running in Development Mode
```bash
cd backend
export FLASK_ENV=development
python3 app.py
```

### Testing the Conversion Pipeline
```bash
# Test Blender installation
blender --version

# Test Wine setup
wine --version

# Test studiomdl.exe
wine /usr/local/wine/cstrike/studiomdl.exe
```

## 🚨 Troubleshooting

### Common Issues

**1. Blender not found**
```bash
which blender
# If not found, check installation path and symlink
```

**2. Wine setup problems**
```bash
# Reinitialize Wine
rm -rf ~/.wine
wineboot --init
```

**3. studiomdl.exe not working**
```bash
# Test directly
wine /usr/local/wine/cstrike/studiomdl.exe -help
```

**4. Permission errors**
```bash
# Check file permissions
ls -la /usr/local/wine/cstrike/studiomdl.exe
sudo chmod +x /usr/local/wine/cstrike/studiomdl.exe
```

### Conversion Failures

**Check the logs:**
- Download the conversion package
- Review `compile.log` for detailed error messages
- Common issues:
  - Bone count exceeds GoldSrc limits (128 bones max)
  - Invalid texture references
  - Malformed FBX structure
  - Missing animations

### Performance Issues

**Optimize for large files:**
- Reduce FBX complexity before upload
- Use appropriate scale settings
- Ensure sufficient RAM (4GB minimum)
- Check disk space availability

## 📋 GoldSrc Compatibility Notes

### Model Limitations
- **Maximum bones**: 128
- **Maximum vertices**: 65535 per mesh
- **Texture size**: Power of 2 (e.g., 256x256, 512x512)
- **Animation frames**: Depends on sequence length

### Best Practices
- Use simple bone hierarchies
- Avoid complex materials
- Bake animations to keyframes
- Use standard bone naming conventions
- Keep texture names simple (no special characters)

## 🔒 Security Features

- **File validation**: Magic number and structure checking
- **Content scanning**: Malicious pattern detection
- **Rate limiting**: IP-based upload restrictions
- **Sandboxing**: Isolated processing environment
- **Input sanitization**: Filename and parameter validation

## 📊 API Endpoints

### Upload File
```
POST /upload
Content-Type: multipart/form-data

Parameters:
- file: FBX file
- scale: Model scale (0.1-100.0)
- bodygroup_name: Bodygroup identifier
```

### Check Status
```
GET /status/<job_id>

Response:
{
  "job_id": "uuid",
  "status": "processing|completed|failed",
  "progress": 0-100,
  "log": ["log entries"],
  "error": "error message if failed"
}
```

### Download Results
```
GET /download/<job_id>

Response: ZIP file with conversion results
```

### Health Check
```
GET /health

Response:
{
  "status": "healthy",
  "active_jobs": 0,
  "total_jobs": 5
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📜 License

This project is provided as-is for educational and development purposes. The GoldSrc SDK and studiomdl.exe are property of Valve Corporation and subject to their respective licenses.

## 🆘 Support

For issues and support:
1. Check the troubleshooting section
2. Review the conversion logs
3. Ensure all dependencies are properly installed
4. Verify FBX file compatibility

## 🔮 Future Enhancements

- **Batch processing**: Multiple file conversion
- **Texture optimization**: Automatic texture resizing
- **Preview system**: 3D model preview before download
- **Discord integration**: Upload notifications
- **Advanced options**: Material settings and optimization
- **Model validation**: Pre-conversion compatibility checking