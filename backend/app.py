# app.py
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import os
import time
import uuid
import threading
import logging
import json
from werkzeug.serving import run_simple
from content_generator.script_gen import generate_script
from content_generator.audio_gen import generate_audio
from content_generator.audio_analyzer import analyze_audio
from content_generator.video_gen import generate_video

try:
    import psutil
except ImportError:
    print("psutil not installed. Process management features will be limited.")
    psutil = None

app = Flask(__name__)
CORS(app)


# Configure logging to ignore certain file changes
class IgnoreFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return not ("debug_script.py" in message or "outputs" in message)

# Apply filter to werkzeug logger
logging.getLogger('werkzeug').addFilter(IgnoreFilter())

UPLOAD_FOLDER = 'static/outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/generate', methods=['POST'])
def generate_content():
    topic = request.json.get('topic')
    if not topic:
        return jsonify({"error": "Topic is required"}), 400
    
    # Generate a unique ID for this request
    request_id = str(uuid.uuid4())
    output_dir = os.path.join(UPLOAD_FOLDER, request_id)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Step 1: Generate script using Gemini
        script = generate_script(topic)
        script_path = os.path.join(output_dir, "script.txt")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        
        # Step 2: Generate audio using gTTS
        audio_path = os.path.join(output_dir, "audio.mp3")
        generate_audio(script, audio_path)
        
        # Step 3: Analyze audio
        timing_data = analyze_audio(audio_path)
        
        # Create a status file to indicate we're processing
        with open(os.path.join(output_dir, "status.txt"), "w") as f:
            f.write("processing")
        
        # Create initial JSON status file
        blender_status_path = os.path.join(output_dir, "blender_status.json")
        with open(blender_status_path, "w") as f:
            json.dump({"status": "starting", "progress": 0, "message": "Initializing video generation"}, f)
        
        # Create a background task to generate the video
        def generate_video_task():
            try:
                # Step 4: Generate video with Blender
                video_path = os.path.join(output_dir, "video.mp4")
                title = f"Learning about {topic}"
                
                # Generate the video
                result = generate_video(script, audio_path, video_path, title)
                
                # Check if the video was generated successfully
                if result:
                    print(f"Video generated successfully: {result}")
                    # Create a status file indicating completion
                    with open(os.path.join(output_dir, "status.txt"), "w") as f:
                        f.write("completed")
                    
                    # Update JSON status
                    with open(blender_status_path, "w") as f:
                        json.dump({"status": "completed", "progress": 100, "message": "Video generation complete"}, f)
                else:
                    print("Video generation failed")
                    # Write error status
                    with open(os.path.join(output_dir, "status.txt"), "w") as f:
                        f.write("error: Failed to generate video")
                    
                    # Update JSON status
                    with open(blender_status_path, "w") as f:
                        json.dump({"status": "error", "progress": 0, "message": "Failed to generate video"}, f)
            
            except Exception as e:
                import traceback
                print(f"Error in background task: {str(e)}")
                traceback.print_exc()
                
                # Write error status
                with open(os.path.join(output_dir, "status.txt"), "w") as f:
                    f.write(f"error: {str(e)}")
                
                # Update JSON status
                with open(blender_status_path, "w") as f:
                    json.dump({"status": "error", "progress": 0, "message": str(e)}, f)
        
        # Start the thread and return immediately
        video_thread = threading.Thread(target=generate_video_task)
        video_thread.daemon = True
        video_thread.start()
        
        # Return paths to the generated content
        return jsonify({
            "success": True,
            "request_id": request_id,
            "script": script
        })
    
    except Exception as e:
        import traceback
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/status/<request_id>', methods=['GET'])
def get_status(request_id):
    output_dir = os.path.join(UPLOAD_FOLDER, request_id)
    if not os.path.exists(output_dir):
        return jsonify({"status": "not_found"}), 404
    
    # Check for Blender's detailed status first
    blender_status_path = os.path.join(output_dir, "blender_status.json")
    if os.path.exists(blender_status_path):
        try:
            with open(blender_status_path, "r") as f:
                status_data = json.load(f)
                
            # If status is completed, return video URL
            if status_data.get("status") == "completed":
                video_path = os.path.join(output_dir, "video.mp4")
                if os.path.exists(video_path):
                    return jsonify({
                        "status": "completed",
                        "video_url": f"/static/outputs/{request_id}/video.mp4",
                        "progress": 100
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "message": "Video processing completed but no file was created",
                        "progress": 0
                    })
            
            # For processing, return progress information
            elif status_data.get("status") == "processing":
                return jsonify({
                    "status": "processing",
                    "progress": status_data.get("progress", 0),
                    "message": status_data.get("message", "")
                })
            
            # For errors, return the error message
            elif status_data.get("status") == "error":
                return jsonify({
                    "status": "error",
                    "message": status_data.get("message", "Unknown error"),
                    "progress": status_data.get("progress", 0)
                })
            
            # Return whatever status is in the file
            return jsonify(status_data)
            
        except Exception as e:
            print(f"Error reading Blender status file: {str(e)}")
    
    # Fall back to the original status checking logic
    status_file = os.path.join(output_dir, "status.txt")
    if os.path.exists(status_file):
        with open(status_file, "r") as f:
            status = f.read().strip()
        
        if status.startswith("error:"):
            return jsonify({"status": "error", "message": status[6:]}), 500
        elif status == "completed":
            return jsonify({
                "status": "completed",
                "video_url": f"/static/outputs/{request_id}/video.mp4"
            })
        elif status == "canceled":
            return jsonify({"status": "canceled"})
    
    # Check if video exists (fallback for older requests)
    video_path = os.path.join(output_dir, "video.mp4")
    if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
        # Update status files to match reality
        with open(status_file, "w") as f:
            f.write("completed")
        with open(blender_status_path, "w") as f:
            json.dump({"status": "completed", "progress": 100, "message": "Video generation complete"}, f)
            
        return jsonify({
            "status": "completed",
            "video_url": f"/static/outputs/{request_id}/video.mp4"
        })
    
    return jsonify({"status": "processing"})

@app.route('/api/cancel/<request_id>', methods=['POST'])
def cancel_generation(request_id):
    output_dir = os.path.join(UPLOAD_FOLDER, request_id)
    if not os.path.exists(output_dir):
        return jsonify({"status": "not_found"}), 404
    
    # Create a cancel file to indicate the process should be canceled
    with open(os.path.join(output_dir, "status.txt"), "w") as f:
        f.write("canceled")
    
    # Update the JSON status file if it exists
    blender_status_path = os.path.join(output_dir, "blender_status.json")
    if os.path.exists(blender_status_path):
        try:
            with open(blender_status_path, "w") as f:
                json.dump({"status": "canceled", "progress": 0, "message": "User canceled the operation"}, f)
        except:
            pass
    
    # Try to kill any running Blender processes
    if psutil:
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if 'blender' in proc.info['name'].lower():
                    try:
                        proc.kill()
                        print(f"Killed Blender process {proc.info['pid']}")
                    except:
                        pass
        except Exception as e:
            print(f"Error trying to kill Blender process: {str(e)}")
    
    return jsonify({"status": "canceled"})

# Modify the serve_file function in app.py to handle path differences better:
@app.route('/static/outputs/<request_id>/<filename>', methods=['GET'])
def serve_file(request_id, filename):
    # Use forward slashes for the directory
    directory = os.path.join(UPLOAD_FOLDER, request_id).replace('\\', '/')
    full_path = os.path.join(directory, filename).replace('\\', '/')
    
    print(f"Attempting to serve file: {full_path}")
    print(f"File exists: {os.path.exists(full_path)}")
    
    if os.path.exists(full_path):
        print(f"File size: {os.path.getsize(full_path)} bytes")
        return send_from_directory(directory, filename)
    else:
        # Search for the file regardless of case
        for file in os.listdir(directory) if os.path.exists(directory) else []:
            if file.lower() == filename.lower():
                return send_from_directory(directory, file)
        
        return f"File not found: {filename}", 404

@app.route('/', methods=['GET'])
def home():
    return """
    <h1>Auto-EduTuber API</h1>
    <p>Use the following endpoints:</p>
    <ul>
        <li><code>POST /api/generate</code> - Generate educational content</li>
        <li><code>GET /api/status/{request_id}</code> - Check generation status</li>
        <li><code>GET /static/outputs/{request_id}/{filename}</code> - Access generated files</li>
        <li><code>POST /api/cancel/{request_id}</code> - Cancel a running generation</li>
    </ul>
    """

if __name__ == '__main__':
    # Install psutil if it's not available
    if psutil is None:
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
            import psutil
            print("Successfully installed psutil")
        except:
            print("Could not install psutil. Continuing without process management.")
    
    app.run(debug=True)