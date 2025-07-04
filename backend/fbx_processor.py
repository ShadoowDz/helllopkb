import os
import subprocess
import tempfile
import logging
import json
import shutil
from pathlib import Path
import re
import math

logger = logging.getLogger(__name__)

class FBXProcessor:
    def __init__(self):
        self.blender_path = "blender"
        self.wine_path = "wine"
        self.studiomdl_path = "/usr/local/wine/cstrike/studiomdl.exe"
        self.temp_dir = None
        
    def convert_fbx_to_mdl(self, fbx_path, output_dir, scale=1.0, bodygroup_name="default", progress_callback=None):
        """
        Main conversion pipeline: FBX -> SMD -> QC -> MDL
        """
        self.temp_dir = tempfile.mkdtemp(prefix="fbx_conversion_")
        
        try:
            result_files = []
            
            # Step 1: Convert FBX to SMD using Blender
            if progress_callback:
                progress_callback(10, "Converting FBX to SMD using Blender...")
            
            smd_files = self._convert_fbx_to_smd(fbx_path, self.temp_dir)
            result_files.extend(smd_files)
            
            # Step 2: Generate QC file
            if progress_callback:
                progress_callback(40, "Generating QC file...")
                
            qc_file = self._generate_qc_file(
                fbx_path, smd_files, self.temp_dir, 
                scale=scale, bodygroup_name=bodygroup_name
            )
            result_files.append(qc_file)
            
            # Step 3: Compile MDL using studiomdl.exe
            if progress_callback:
                progress_callback(60, "Compiling MDL file...")
                
            mdl_files = self._compile_mdl(qc_file, self.temp_dir)
            result_files.extend(mdl_files)
            
            # Step 4: Copy results to output directory
            if progress_callback:
                progress_callback(90, "Copying results...")
                
            final_files = []
            for file_path in result_files:
                if os.path.exists(file_path):
                    dest_path = os.path.join(output_dir, os.path.basename(file_path))
                    shutil.copy2(file_path, dest_path)
                    final_files.append(dest_path)
            
            if progress_callback:
                progress_callback(100, "Conversion completed!")
                
            return {
                'success': True,
                'files': final_files,
                'message': 'FBX converted to MDL successfully'
            }
            
        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'files': []
            }
        finally:
            # Clean up temporary directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _convert_fbx_to_smd(self, fbx_path, output_dir):
        """Convert FBX to SMD using Blender with Source Tools addon"""
        
        # Create Blender Python script for conversion
        blender_script = self._create_blender_script(fbx_path, output_dir)
        script_path = os.path.join(output_dir, "convert_script.py")
        
        with open(script_path, 'w') as f:
            f.write(blender_script)
        
        # Run Blender in headless mode
        cmd = [
            self.blender_path,
            "--background",
            "--python", script_path,
            "--", fbx_path, output_dir
        ]
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300,  # 5 minute timeout
                cwd=output_dir
            )
            
            if result.returncode != 0:
                raise Exception(f"Blender conversion failed: {result.stderr}")
            
            # Find generated SMD files
            smd_files = []
            for file in os.listdir(output_dir):
                if file.endswith('.smd'):
                    smd_files.append(os.path.join(output_dir, file))
            
            if not smd_files:
                raise Exception("No SMD files were generated")
            
            return smd_files
            
        except subprocess.TimeoutExpired:
            raise Exception("Blender conversion timed out")
        except Exception as e:
            raise Exception(f"Blender conversion error: {str(e)}")
    
    def _create_blender_script(self, fbx_path, output_dir):
        """Create Blender Python script for FBX to SMD conversion"""
        return f'''
import bpy
import bmesh
import os
import sys

def clear_scene():
    """Clear all objects from scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def import_fbx(filepath):
    """Import FBX file"""
    try:
        bpy.ops.import_scene.fbx(filepath=filepath, use_anim=True)
        print(f"Successfully imported FBX: {{filepath}}")
        return True
    except Exception as e:
        print(f"Error importing FBX: {{e}}")
        return False

def setup_source_tools():
    """Enable Source Tools addon if available"""
    try:
        bpy.ops.preferences.addon_enable(module="io_scene_valvesource")
        print("Source Tools addon enabled")
        return True
    except:
        print("Warning: Source Tools addon not found, using fallback method")
        return False

def export_to_smd(output_dir):
    """Export scene to SMD format"""
    # Get the base name from FBX
    base_name = "model"
    
    # Try to export using Source Tools if available
    try:
        # Export reference SMD (mesh)
        ref_path = os.path.join(output_dir, f"{{base_name}}_ref.smd")
        bpy.ops.export_scene.smd(
            filepath=ref_path,
            export_animations=False,
            export_triangles=True
        )
        print(f"Exported reference SMD: {{ref_path}}")
        
        # Export animation SMDs if animations exist
        if bpy.data.actions:
            for action in bpy.data.actions:
                anim_path = os.path.join(output_dir, f"{{base_name}}_{{action.name}}.smd")
                # Set current action
                if bpy.context.object and bpy.context.object.animation_data:
                    bpy.context.object.animation_data.action = action
                
                bpy.ops.export_scene.smd(
                    filepath=anim_path,
                    export_animations=True,
                    export_triangles=False
                )
                print(f"Exported animation SMD: {{anim_path}}")
        else:
            # Create idle animation
            idle_path = os.path.join(output_dir, f"{{base_name}}_idle.smd")
            bpy.ops.export_scene.smd(
                filepath=idle_path,
                export_animations=True,
                export_triangles=False
            )
            print(f"Exported idle animation SMD: {{idle_path}}")
            
    except Exception as e:
        print(f"Source Tools export failed, using fallback: {{e}}")
        # Fallback: create basic SMD manually
        create_basic_smd(output_dir, base_name)

def create_basic_smd(output_dir, base_name):
    """Create basic SMD file manually when Source Tools isn't available"""
    ref_path = os.path.join(output_dir, f"{{base_name}}_ref.smd")
    
    with open(ref_path, 'w') as f:
        f.write("version 1\\n")
        f.write("nodes\\n")
        f.write("0 \\"root\\" -1\\n")
        f.write("end\\n")
        f.write("skeleton\\n")
        f.write("time 0\\n")
        f.write("0 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000\\n")
        f.write("end\\n")
        f.write("triangles\\n")
        
        # Export mesh data
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                mesh = obj.data
                # Apply modifiers
                depsgraph = bpy.context.evaluated_depsgraph_get()
                obj_eval = obj.evaluated_get(depsgraph)
                mesh_eval = obj_eval.data
                
                # Get vertex data
                mesh_eval.calc_loop_triangles()
                for tri in mesh_eval.loop_triangles:
                    material_name = "default"
                    if obj.material_slots and tri.material_index < len(obj.material_slots):
                        material = obj.material_slots[tri.material_index].material
                        if material:
                            material_name = material.name
                    
                    f.write(f"{{material_name}}\\n")
                    
                    for loop_index in tri.loops:
                        loop = mesh_eval.loops[loop_index]
                        vertex = mesh_eval.vertices[loop.vertex_index]
                        
                        # Transform vertex to world space
                        world_vertex = obj.matrix_world @ vertex.co
                        
                        # Get UV coordinates if available
                        uv = [0.0, 0.0]
                        if mesh_eval.uv_layers:
                            uv_layer = mesh_eval.uv_layers.active.data
                            uv = uv_layer[loop_index].uv
                        
                        # Get normal
                        normal = vertex.normal
                        world_normal = obj.matrix_world.to_3x3() @ normal
                        world_normal.normalize()
                        
                        # Write vertex data
                        f.write(f"0 {{world_vertex.x:.6f}} {{world_vertex.y:.6f}} {{world_vertex.z:.6f}} ")
                        f.write(f"{{world_normal.x:.6f}} {{world_normal.y:.6f}} {{world_normal.z:.6f}} ")
                        f.write(f"{{uv[0]:.6f}} {{uv[1]:.6f}}\\n")
        
        f.write("end\\n")
    
    print(f"Created basic SMD: {{ref_path}}")
    
    # Create idle animation
    idle_path = os.path.join(output_dir, f"{{base_name}}_idle.smd")
    with open(idle_path, 'w') as f:
        f.write("version 1\\n")
        f.write("nodes\\n")
        f.write("0 \\"root\\" -1\\n")
        f.write("end\\n")
        f.write("skeleton\\n")
        f.write("time 0\\n")
        f.write("0 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000\\n")
        f.write("time 1\\n")
        f.write("0 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000\\n")
        f.write("end\\n")
    
    print(f"Created idle animation: {{idle_path}}")

def main():
    try:
        if len(sys.argv) < 2:
            print("Usage: blender --background --python script.py -- <fbx_file> <output_dir>")
            return
        
        fbx_file = sys.argv[-2]
        output_dir = sys.argv[-1]
        
        print(f"Processing: {{fbx_file}} -> {{output_dir}}")
        
        # Clear scene
        clear_scene()
        
        # Setup Source Tools if available
        setup_source_tools()
        
        # Import FBX
        if not import_fbx(fbx_file):
            raise Exception("Failed to import FBX file")
        
        # Export to SMD
        export_to_smd(output_dir)
        
        print("Conversion completed successfully!")
        
    except Exception as e:
        print(f"Error in main: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    def _generate_qc_file(self, fbx_path, smd_files, output_dir, scale=1.0, bodygroup_name="default"):
        """Generate QC file for studiomdl compilation"""
        
        base_name = os.path.splitext(os.path.basename(fbx_path))[0]
        qc_path = os.path.join(output_dir, f"{base_name}.qc")
        
        # Find reference and animation SMD files
        ref_smd = None
        anim_smds = []
        
        for smd_file in smd_files:
            filename = os.path.basename(smd_file)
            if "_ref" in filename or filename.endswith("_ref.smd"):
                ref_smd = filename
            else:
                anim_smds.append(filename)
        
        # If no reference SMD found, use the first one
        if not ref_smd and smd_files:
            ref_smd = os.path.basename(smd_files[0])
        
        with open(qc_path, 'w') as qc:
            # Header
            qc.write(f'$modelname "{base_name}.mdl"\n')
            qc.write(f'$cd "."\n')
            qc.write(f'$cdtexture "."\n')
            qc.write(f'$scale {scale}\n\n')
            
            # Body definition
            if ref_smd:
                qc.write(f'$body "{bodygroup_name}" "{ref_smd}"\n\n')
            
            # Sequences (animations)
            if anim_smds:
                for anim_smd in anim_smds:
                    anim_name = os.path.splitext(anim_smd)[0]
                    # Remove model name prefix if present
                    if anim_name.startswith(base_name + "_"):
                        anim_name = anim_name[len(base_name) + 1:]
                    
                    qc.write(f'$sequence "{anim_name}" "{anim_smd}" fps 30\n')
            else:
                # Default idle sequence
                if ref_smd:
                    qc.write(f'$sequence "idle" "{ref_smd}" fps 30\n')
            
            qc.write('\n')
            
            # Common GoldSrc settings
            qc.write('// GoldSrc compatibility settings\n')
            qc.write('$flags 0\n')
            qc.write('$origin 0 0 0\n')
            qc.write('$eyeposition 0 0 0\n')
            qc.write('$bbox 0 0 0 0 0 0\n')
            qc.write('$cbox 0 0 0 0 0 0\n')
            
            # Texture settings
            qc.write('\n// Texture settings\n')
            qc.write('$texrendermode "default.bmp" masked\n')
            qc.write('$texrendermode "default" masked\n')
        
        return qc_path
    
    def _compile_mdl(self, qc_file, output_dir):
        """Compile MDL file using studiomdl.exe via Wine"""
        
        # Check if studiomdl.exe exists
        if not os.path.exists(self.studiomdl_path):
            raise Exception(f"studiomdl.exe not found at {self.studiomdl_path}")
        
        # Prepare Wine environment
        wine_env = os.environ.copy()
        wine_env['WINEPATH'] = '/usr/local/wine/cstrike'
        wine_env['WINEPREFIX'] = os.path.expanduser('~/.wine')
        
        # Run studiomdl.exe
        cmd = [
            self.wine_path,
            self.studiomdl_path,
            os.path.basename(qc_file)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
                env=wine_env
            )
            
            # Create compile log
            log_path = os.path.join(output_dir, "compile.log")
            with open(log_path, 'w') as log_file:
                log_file.write("=== STUDIOMDL COMPILATION LOG ===\n")
                log_file.write(f"Command: {' '.join(cmd)}\n")
                log_file.write(f"Return code: {result.returncode}\n\n")
                log_file.write("=== STDOUT ===\n")
                log_file.write(result.stdout)
                log_file.write("\n=== STDERR ===\n")
                log_file.write(result.stderr)
            
            if result.returncode != 0:
                raise Exception(f"studiomdl compilation failed. Check compile.log for details.")
            
            # Find generated files
            generated_files = []
            base_name = os.path.splitext(os.path.basename(qc_file))[0]
            
            # Common MDL output files
            possible_extensions = ['.mdl', '.mdl.vtx', '.phy', '.vvd']
            
            for ext in possible_extensions:
                file_path = os.path.join(output_dir, base_name + ext)
                if os.path.exists(file_path):
                    generated_files.append(file_path)
            
            # Always include the log file
            generated_files.append(log_path)
            
            if not any(f.endswith('.mdl') for f in generated_files):
                raise Exception("No MDL file was generated")
            
            return generated_files
            
        except subprocess.TimeoutExpired:
            raise Exception("studiomdl compilation timed out")
        except Exception as e:
            raise Exception(f"studiomdl compilation error: {str(e)}")
    
    def validate_requirements(self):
        """Validate that required tools are available"""
        errors = []
        
        # Check Blender
        try:
            result = subprocess.run([self.blender_path, "--version"], 
                                  capture_output=True, timeout=10)
            if result.returncode != 0:
                errors.append("Blender not found or not working")
        except:
            errors.append("Blender not found or not working")
        
        # Check Wine
        try:
            result = subprocess.run([self.wine_path, "--version"], 
                                  capture_output=True, timeout=10)
            if result.returncode != 0:
                errors.append("Wine not found or not working")
        except:
            errors.append("Wine not found or not working")
        
        # Check studiomdl.exe
        if not os.path.exists(self.studiomdl_path):
            errors.append(f"studiomdl.exe not found at {self.studiomdl_path}")
        
        return len(errors) == 0, errors