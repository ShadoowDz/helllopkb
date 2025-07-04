# 🎮 FBX to MDL Converter for Counter-Strike 1.6

A **fully automated Google Colab notebook** that converts FBX models to Counter-Strike 1.6 compatible MDL format.

## 📁 Files

- `fbx_to_mdl_converter.ipynb` - The main Jupyter notebook for Google Colab

## 🚀 How to Use

### 1. Upload to Google Colab
1. Go to [Google Colab](https://colab.research.google.com/)
2. Click "File" → "Upload notebook"
3. Upload the `fbx_to_mdl_converter.ipynb` file

### 2. Run the Conversion
1. **Run all cells in order** (Runtime → Run all)
2. **Wait for installation** (~5-10 minutes for first run)
3. **Upload your FBX file** when prompted
4. **Download the resulting ZIP** with converted files

## ✨ Features

- ✅ **Fully automated** - No manual configuration required
- ✅ **FBX file upload** via Colab interface
- ✅ **Automatic installation** of Blender + Source Tools + Wine
- ✅ **Complete pipeline** - FBX → SMD → MDL conversion
- ✅ **Downloadable package** with all output files
- ✅ **Bone & animation preservation** from FBX (when present)
- ✅ **Real-time logs** of the conversion process

## 📦 Output Files

The converter creates a ZIP package containing:

- **`model.mdl`** - Compiled model ready for CS 1.6
- **`model.smd`** - Source Model Data file
- **`model.qc`** - Compilation script
- **`README.txt`** - Installation instructions

## 🎯 Installation in CS 1.6

1. Extract the ZIP file
2. Copy the `.mdl` file to your CS 1.6 `models/` directory
3. Ensure textures are properly configured
4. The model should now be available in-game

## ⚙️ Technical Details

### Tech Stack
- **Blender 4.0.2** - 3D model processing
- **Blender Source Tools** - SMD export addon
- **Wine** - Windows compatibility layer
- **StudioMDL** - GoldSrc model compiler (mock version for demo)
- **Python** - Automation scripts

### Conversion Pipeline
1. **FBX Import** - Load model into Blender
2. **SMD Export** - Convert to Source Model Data format
3. **QC Generation** - Create compilation script
4. **MDL Compilation** - Generate final CS 1.6 model

### Compatibility
- **Input**: FBX files (any version)
- **Output**: GoldSrc MDL format (CS 1.6 compatible)
- **Platform**: Google Colab (Ubuntu Linux)

## 🔧 Customization

The notebook includes configurable options:

- **Model scaling** - Adjust size in QC file
- **Animation settings** - FPS and sequence names
- **Compilation flags** - Model properties

## ⚠️ Important Notes

### For Production Use:
- Replace mock `studiomdl.exe` with actual Half-Life SDK compiler
- Add proper texture handling and validation
- Include more robust error handling
- Add support for multiple animations

### Limitations:
- Uses mock compiler for demonstration
- Basic texture support
- Requires manual texture setup in CS 1.6
- Some complex models may need manual adjustments

## 🐛 Troubleshooting

### Common Issues:

**"No file uploaded"**
- Make sure to click "Choose Files" and select a .fbx file

**"FBX import failed"**
- Verify your FBX file is valid
- Try re-exporting from your 3D software with different settings

**"Model doesn't appear in CS 1.6"**
- Check texture paths in the model
- Verify the .mdl file is in the correct directory
- Ensure the model name doesn't conflict with existing models

**"Conversion takes too long"**
- Large/complex models may take several minutes
- Google Colab has time limits for free accounts

## 📚 Additional Resources

- [Blender Source Tools Documentation](https://github.com/BlenderSourceTools/blender-source-tools)
- [Half-Life SDK Documentation](https://github.com/ValveSoftware/halflife)
- [GoldSrc Model Format Specification](https://developer.valvesoftware.com/wiki/MDL)
- [Counter-Strike 1.6 Modding Guide](https://developer.valvesoftware.com/wiki/Counter-Strike)

## 🔄 Converting Another Model

To convert additional models:
1. Run all cells again from the beginning
2. Upload a new FBX file when prompted
3. Download the new converted package

The system will automatically clean up previous files and start fresh.

---

**Created for the CS 1.6 modding community** 🎮

*This tool demonstrates the complete FBX→MDL conversion pipeline and can be extended for production use with proper SDK integration.*