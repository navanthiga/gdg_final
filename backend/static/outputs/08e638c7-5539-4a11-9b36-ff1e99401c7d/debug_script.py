
import bpy
import os
import math
import random

print("Educational video Blender script started")

# Clear default objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create a nice cream-colored background
world = bpy.data.worlds["World"]
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.96, 0.95, 0.86, 1)  # Cream color

# Set up camera first (so we can see what we're doing)
bpy.ops.object.camera_add(location=(0, -8, 0))
camera = bpy.context.active_object
camera.rotation_euler = (1.5708, 0, 0)  # 90 degrees X rotation
bpy.context.scene.camera = camera

# Add a light
bpy.ops.object.light_add(type='SUN', location=(5, -5, 5))
light = bpy.context.active_object
light.data.energy = 3

# Add more lights for better visibility
bpy.ops.object.light_add(type='POINT', location=(-5, -5, 5))
fill_light = bpy.context.active_object
fill_light.data.energy = 300

# Add text for title
bpy.ops.object.text_add(location=(0, 1, 0))
title_obj = bpy.context.active_object
title_obj.data.body = "Learning about sun"
title_obj.data.size = 1.0
title_obj.data.align_x = 'CENTER'
title_obj.data.extrude = 0.1  # Add some extrusion to make it more visible

# Add material to title
title_mat = bpy.data.materials.new(name="TitleMat")
title_mat.use_nodes = True
title_principled = title_mat.node_tree.nodes.get('Principled BSDF')
title_principled.inputs[0].default_value = (0.1, 0.3, 0.8, 1)  # Blue
title_obj.data.materials.append(title_mat)

# Add a cube to the right of the title
bpy.ops.mesh.primitive_cube_add(size=1.2, location=(3, 0, 0))
cube = bpy.context.active_object

# Add material to cube
cube_mat = bpy.data.materials.new(name="CubeMat")
cube_mat.use_nodes = True
cube_principled = cube_mat.node_tree.nodes.get('Principled BSDF')
cube_principled.inputs[0].default_value = (0.8, 0.2, 0.2, 1)  # Red
cube.data.materials.append(cube_mat)

# Animate the cube
cube.animation_data_create()
cube.rotation_euler = (0, 0, 0)
cube.keyframe_insert(data_path="rotation_euler", frame=1)
cube.rotation_euler = (0, 0, 6.28)  # Full rotation (360 degrees)
cube.keyframe_insert(data_path="rotation_euler", frame=1440)

# Add another animation to the cube
cube.scale = (1, 1, 1)
cube.keyframe_insert(data_path="scale", frame=1)
cube.scale = (1.5, 1.5, 1.5)
cube.keyframe_insert(data_path="scale", frame=int(1440/2))
cube.scale = (1, 1, 1)
cube.keyframe_insert(data_path="scale", frame=1440)

# Add a sphere to the left of the title
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.7, location=(-3, 0, 0))
sphere = bpy.context.active_object

# Add material to sphere
sphere_mat = bpy.data.materials.new(name="SphereMat")
sphere_mat.use_nodes = True
sphere_principled = sphere_mat.node_tree.nodes.get('Principled BSDF')
sphere_principled.inputs[0].default_value = (0.2, 0.8, 0.2, 1)  # Green
sphere.data.materials.append(sphere_mat)

# Animate the sphere - bouncing motion
sphere.animation_data_create()
sphere.location = (-3, 0, 0)
sphere.keyframe_insert(data_path="location", frame=1)

# Create multiple bounces based on duration
bounce_cycles = max(1, int(60 / 5))  # One bounce every ~5 seconds
for i in range(bounce_cycles):
    # Up
    frame_up = int(1 + (i * 1440 / bounce_cycles))
    sphere.location = (-3, 0, 1.5)
    sphere.keyframe_insert(data_path="location", frame=frame_up)
    
    # Down
    frame_down = int(1 + ((i + 0.5) * 1440 / bounce_cycles))
    sphere.location = (-3, 0, 0)
    sphere.keyframe_insert(data_path="location", frame=frame_down)

# Add a cone for visual interest
bpy.ops.mesh.primitive_cone_add(radius1=0.6, radius2=0, depth=1.2, location=(0, -3, 0))
cone = bpy.context.active_object

# Add material to cone
cone_mat = bpy.data.materials.new(name="ConeMat")
cone_mat.use_nodes = True
cone_principled = cone_mat.node_tree.nodes.get('Principled BSDF')
cone_principled.inputs[0].default_value = (0.8, 0.6, 0.1, 1)  # Orange/Gold
cone.data.materials.append(cone_mat)

# Animate the cone - spinning
cone.animation_data_create()
cone.rotation_euler = (0, 0, 0)
cone.keyframe_insert(data_path="rotation_euler", frame=1)
cone.rotation_euler = (0, 6.28, 0)  # Full Y rotation
cone.keyframe_insert(data_path="rotation_euler", frame=1440)

# Add a plane for the floor
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -1.5))
floor = bpy.context.active_object

# Add material to floor
floor_mat = bpy.data.materials.new(name="FloorMat")
floor_mat.use_nodes = True
floor_principled = floor_mat.node_tree.nodes.get('Principled BSDF')
floor_principled.inputs[0].default_value = (0.3, 0.3, 0.3, 1)  # Gray
floor.data.materials.append(floor_mat)

# Process script text for sentence extraction - simplified approach
sentences = []
for sentence in "Ever wondered about that giant, blazing ball of light in the sky?  It's more than just a source of warmth; it's the Sun, the star at the center of our solar system, and it's truly amazing!  Let's explore some fascinating facts about it.  First, the Sun is HUGE.  Imagine a million Earths fitting inside - that's how big it is!  This enormous size creates immense gravity, holding all the planets in our solar system in their orbits, including us.  Second, the Sun is incredibly hot. Its core reaches temperatures of about 27 million degrees Fahrenheit! This intense heat is generated by nuclear fusion, where hydrogen atoms are smashed together to form helium, releasing enormous amounts of energy in the process. This energy travels outwards as light and heat, reaching us here on Earth.  Third, sunlight is essential for life. Plants use sunlight for photosynthesis, creating the oxygen we breathe and the food we eat.  It also provides us with Vitamin D, crucial for healthy bones and immune systems.  Imagine our world without the Sun - dark, cold, and lifeless.  Finally, even though the Sun appears unchanging in the sky, it's a dynamic and active star.  It has sunspots, which are cooler, darker areas on its surface caused by magnetic activity.  It also produces solar flares, bursts of energy that can sometimes disrupt our technology here on Earth.  So, the Sun - a massive, hot, life-giving star, constantly changing and impacting our planet.  It's a powerful reminder of the vastness of space and the intricate connections within our solar system. ".split('. '):
    if sentence.strip():
        sentences.append(sentence.strip() + '.')

# Add a container/background for the script text
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 3, -1))
text_bg = bpy.context.active_object
text_bg.rotation_euler = (1.5708, 0, 0)  # 90 degrees X rotation

# Add material to text background
text_bg_mat = bpy.data.materials.new(name="TextBgMat")
text_bg_mat.use_nodes = True
text_bg_principled = text_bg_mat.node_tree.nodes.get('Principled BSDF')
text_bg_principled.inputs[0].default_value = (0.9, 0.9, 0.9, 1)  # Light gray
text_bg.data.materials.append(text_bg_mat)

# Calculate how long each sentence should be displayed based on audio segments
frames_per_segment = []
for segment in [{'start': 0.0, 'end': 20.0, 'duration': 20.0}, {'start': 20.0, 'end': 40.0, 'duration': 20.0}, {'start': 40.0, 'end': 60, 'duration': 20.0}]:
    segment_frames = int(segment["duration"] * 24)
    frames_per_segment.append(segment_frames)

# Use segments to time text display
segment_count = len([{'start': 0.0, 'end': 20.0, 'duration': 20.0}, {'start': 20.0, 'end': 40.0, 'duration': 20.0}, {'start': 40.0, 'end': 60, 'duration': 20.0}])
sentences_per_segment = max(1, len(sentences) // segment_count)
current_frame = 1

# Create text objects for each sentence
for i, sentence in enumerate(sentences):
    if i >= 20:  # Limit the number of sentences to prevent issues
        break
        
    # Calculate which segment this sentence belongs to
    segment_index = min(i // sentences_per_segment, segment_count - 1)
    
    # Calculate frame timing
    if segment_index < len(frames_per_segment):
        frame_duration = max(24, frames_per_segment[segment_index] // sentences_per_segment)
        start_offset = (i % sentences_per_segment) * frame_duration
        segment_start = sum(frames_per_segment[:segment_index])
        
        display_start = segment_start + start_offset
        display_end = display_start + frame_duration
    else:
        # Fallback timing if segments don't align perfectly
        frame_duration = max(24, 1440 // len(sentences))
        display_start = i * frame_duration
        display_end = (i + 1) * frame_duration
    
    # Create text object
    bpy.ops.object.text_add(location=(0, 3, -0.9))
    text_obj = bpy.context.active_object
    
    # Limit sentence length to avoid potential issues
    if len(sentence) > 80:
        sentence = sentence[:77] + "..."
    
    text_obj.data.body = sentence
    text_obj.data.size = 0.4
    text_obj.data.align_x = 'CENTER'
    text_obj.rotation_euler = (1.5708, 0, 0)  # 90 degrees X rotation
    
    # Add material
    text_mat = bpy.data.materials.new(name=f"TextMat_{i}")
    text_mat.use_nodes = True
    text_principled = text_mat.node_tree.nodes.get('Principled BSDF')
    text_principled.inputs[0].default_value = (0.1, 0.1, 0.1, 1)  # Dark gray
    text_obj.data.materials.append(text_mat)
    
    # Animate visibility
    # Start off-screen
    text_obj.location.z = -5  
    text_obj.keyframe_insert(data_path="location", frame=1)
    
    # Move on-screen
    text_obj.location.z = -0.9
    text_obj.keyframe_insert(data_path="location", frame=display_start)
    
    # Stay visible
    text_obj.location.z = -0.9
    text_obj.keyframe_insert(data_path="location", frame=display_end)
    
    # Move off-screen
    text_obj.location.z = 3
    text_obj.keyframe_insert(data_path="location", frame=display_end + 1)

# Add audio to the scene
bpy.context.scene.sequence_editor_create()
sound_strip = bpy.context.scene.sequence_editor.sequences.new_sound(
    name="Audio",
    filepath=r"static/outputs\\08e638c7-5539-4a11-9b36-ff1e99401c7d\\audio.mp3",
    channel=1,
    frame_start=1
)

# Set render settings
scene = bpy.context.scene
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100

# Check available render engines
available_engines = {'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH', 'CYCLES'}

# Use EEVEE if available
if 'BLENDER_EEVEE' in available_engines:
    scene.render.engine = 'BLENDER_EEVEE'
elif 'BLENDER_EEVEE_NEXT' in available_engines:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
elif 'CYCLES' in available_engines:
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32  # Lower samples for faster rendering
else:
    scene.render.engine = 'BLENDER_WORKBENCH'

print(f"Using render engine: {scene.render.engine}")

scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 1440  # Set end frame based on audio duration

# FFmpeg settings
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
scene.render.ffmpeg.ffmpeg_preset = 'GOOD'

# Set output path
scene.render.filepath = r"static/outputs\\08e638c7-5539-4a11-9b36-ff1e99401c7d\\video.mp4"

print(f"Rendering educational video to: {scene.render.filepath}")
print(f"Resolution: {scene.render.resolution_x}x{scene.render.resolution_y}")
print(f"Frames: {scene.frame_start}-{scene.frame_end} at {scene.render.fps}fps")
print(f"Audio path: {sound_strip.filepath}")

# Render animation
bpy.ops.render.render(animation=True)

print("Educational video rendering complete!")
