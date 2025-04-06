import os
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import *
from gtts import gTTS
from IPython.display import display, HTML
from base64 import b64encode
import google.generativeai as genai

import requests
from io import BytesIO


from duckduckgo_search import DDGS  # Correct import for latest version
from duckduckgo_search import DDGS
import requests
from PIL import Image
from io import BytesIO
import concurrent.futures
import time

# Cache to store already downloaded images
IMAGE_CACHE = {}
REQUEST_TIMEOUT = 5  # seconds
MAX_WORKERS = 4  # For parallel downloads

def download_image_ddg(keyword):
    """Optimized image downloader with caching and timeout"""
    # Check cache first
    if keyword in IMAGE_CACHE:
        return IMAGE_CACHE[keyword]
    
    try:
        start_time = time.time()
        
        # Initialize DDGS only when needed
        with DDGS() as ddgs:
            # Get first image result with timeout
            for result in ddgs.images(keyword, max_results=1):
                img_url = result["image"]
                
                # Download with timeout
                response = requests.get(img_url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                
                img = Image.open(BytesIO(response.content))
                resized_img = img.resize((600, 400), Image.Resampling.LANCZOS)
                
                # Cache the image
                IMAGE_CACHE[keyword] = resized_img
                print(f"Downloaded '{keyword}' in {time.time()-start_time:.2f}s")
                return resized_img
                
    except Exception as e:
        print(f"Image download failed for '{keyword}': {str(e)}")
        # Return a placeholder if download fails
        placeholder = Image.new('RGB', (600, 400), color=(73, 109, 137))
        IMAGE_CACHE[keyword] = placeholder
        return placeholder

def preload_images(keywords):
    """Preload images in parallel before video generation starts"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(download_image_ddg, keywords)

def create_section_slide(title, content, duration, color, image_keyword=None):
    """Updated slide creation with DuckDuckGo images"""
    def make_frame(t):
        # Create background
        frame = np.zeros((VIDEO_SIZE[1], VIDEO_SIZE[0], 3), dtype=np.uint8)
        try:
            hex_color = color.lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            frame[:] = rgb
        except:
            frame[:] = (65, 105, 225)  # Fallback color

        img_pil = Image.fromarray(frame)
        draw = ImageDraw.Draw(img_pil)

        # Load fonts
        try:
            title_font = ImageFont.truetype(FONT_PATH, 50)
            content_font = ImageFont.truetype(FONT_PATH, 32)
        except:
            title_font = ImageFont.load_default(size=50)
            content_font = ImageFont.load_default(size=32)

        # Draw title (centered)
        title_width = title_font.getlength(title)
        title_x = (VIDEO_SIZE[0] - title_width) // 2
        draw.text((title_x, 60), title, font=title_font, fill="white")

        # Wrap and draw content (left side)
        margin_x = 80
        max_width = VIDEO_SIZE[0] // 2 - margin_x
        y_pos = 150
        line_height = 40

        words = content.split()
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            if content_font.getlength(test_line) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    draw.text((margin_x, y_pos), ' '.join(current_line),
                             font=content_font, fill="white")
                    y_pos += line_height
                current_line = [word]
                if y_pos > VIDEO_SIZE[1] - 100:
                    break

        if current_line and y_pos <= VIDEO_SIZE[1] - 100:
            draw.text((margin_x, y_pos), ' '.join(current_line),
                     font=content_font, fill="white")

        # Add image from DuckDuckGo (right side)
        if image_keyword:
            try:
                img = download_image_ddg(image_keyword)
                if img:
                    img_x = VIDEO_SIZE[0] // 2 + 50
                    img_y = 100
                    img_pil.paste(img, (img_x, img_y))
                    
                    # Add attribution text
                    attribution_font = ImageFont.load_default(size=14)
                    draw.text((img_x + 20, VIDEO_SIZE[1] - 40),
                             f"Image: {image_keyword} (Source: DuckDuckGo)",
                             font=attribution_font, fill="white")
                else:
                    # Fallback placeholder if image fails
                    draw.rectangle([(img_x, 100), (img_x + (VIDEO_SIZE[0]//2 - 100), 
                                  VIDEO_SIZE[1] - 50)], outline="white", width=3)
                    draw.text((img_x + 20, VIDEO_SIZE[1] - 40),
                             f"Image: {image_keyword} (Not loaded)",
                             font=ImageFont.load_default(size=24), fill="white")
            except Exception as e:
                print(f"Image processing error: {e}")

        return np.array(img_pil)

    return VideoClip(make_frame, duration=duration)

# (Rest of your original functions remain unchanged)

def display_video(video_path):
    """Display the generated video in notebook"""
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    with open(video_path, 'rb') as f:
        mp4 = f.read()
    data_url = "data:video/mp4;base64," + b64encode(mp4).decode()
    display(HTML(f'<video width=640 controls><source src="{data_url}" type="video/mp4"></video>'))

def get_structured_content(topic):
    """Get content from Gemini API with proper error handling"""
    prompt = f"""
    Create a video script about '{topic}' with the following structure:
    1. An introduction/overview
    2. Three to five key points about {topic}
    3. An interesting fact
    4. A conclusion

    For each section, format your response EXACTLY as follows (include the square brackets):

    [Title]: (write title here)
    [Content]: (write 2-3 sentences of content here)
    [ImageKeyword]: (write a keyword for image search here)

    Repeat this exact structure for each section. Do not deviate from this format.
    and do not add any symbols in the script like ** or ##.
    """
    try:
        for model_name in ['gemini-1.5-pro', 'gemini-pro']:
            try:
                print(f"Attempting to generate content using model: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(
                    prompt,
                    generation_config={"temperature": 0.3}
                )

                if not response or not hasattr(response, 'text'):
                    print(f"No valid response from model {model_name}")
                    continue

                print("Successfully generated content from Gemini")
                return parse_gemini_response(response.text)

            except Exception as e:
                print(f"Error with model {model_name}: {str(e)}")
                if "API key not valid" in str(e):
                    print("Please check your Gemini API key configuration")
                    return None
                continue

        print("Error: Failed to get valid response from all available models")
        return None

    except Exception as e:
        print(f"Gemini API connection error: {str(e)}")
        return None


def parse_gemini_response(text):
    """Enhanced parser that extracts titles, content and image keywords"""
    sections = []
    current_section = None

    # Split into sections
    section_blocks = re.split(r'(?:^|\n)\[Title\]:', text.strip())

    for block in section_blocks[1:]:  # Skip first empty block
        lines = block.strip().split('\n')
        if len(lines) < 2:
            continue

        title = lines[0].strip()
        content = ""
        image_keyword = ""

        for line in lines[1:]:
            if line.strip().startswith('[Content]:'):
                content = line.replace('[Content]:', '').strip()
            elif line.strip().startswith('[ImageKeyword]:'):
                image_keyword = line.replace('[ImageKeyword]:', '').strip()

        if title and content:
            sections.append({
                'title': title,
                'content': content,
                'image_keyword': image_keyword
            })

    # Fallback if no sections found
    if not sections:
        parts = re.split(r'\n\n+', text)
        sections = [{
            'title': f"Section {i+1}",
            'content': part.strip(),
            'image_keyword': topic.lower()  # Use topic as fallback keyword
        } for i, part in enumerate(parts[:4])]

    return sections

def create_animated_background(t, duration):
    """Create background with fixed color for reliability"""
    frame = np.zeros((VIDEO_SIZE[1], VIDEO_SIZE[0], 3), dtype=np.uint8)
    frame[:] = (65, 105, 225)  # Royal blue
    return frame

def create_title_slide(topic, duration=4):
    """Create title slide with reliable text rendering"""
    def make_frame(t):
        frame = create_animated_background(t, duration)
        img_pil = Image.fromarray(frame)
        draw = ImageDraw.Draw(img_pil)

        try:
            font = ImageFont.truetype(FONT_PATH, 60)
        except:
            font = ImageFont.load_default(size=60)

        title = f"The Science of\n{topic.title()}"
        draw.text((VIDEO_SIZE[0]//2, VIDEO_SIZE[1]//2 - 50), title,
                 font=font, fill="white", anchor="mm")
        draw.text((VIDEO_SIZE[0]//2, VIDEO_SIZE[1]//2 + 50), "A Student's Guide",
                 font=font, fill="#DDDDFF", anchor="mm")

        return np.array(img_pil)

    return VideoClip(make_frame, duration=duration)



def text_to_speech(text, output_file):
    """Convert text to speech with error handling"""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_file)
        return AudioFileClip(output_file)
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

def generate_science_video(topic, output_file="science_video.mp4"):
    #def generate_science_video(topic, output_file="science_video.mp4"):
    """Main function with improved audio and slides"""
    print(f"Generating video about {topic}...")

    # Get structured content
    sections = get_structured_content(topic)
    if not sections:
        sections = [{
            'title': f"Introduction to {topic}",
            'content': f"This is an introduction to {topic}.",
            'image_keyword': topic.lower()
        }, {
            'title': f"About {topic}",
            'content': f"Here are some key facts about {topic}.",
            'image_keyword': topic.lower()
        }]

    # Generate video
    clips = [create_title_slide(topic)]
    audio_clips = []
    current_time = clips[0].duration

    # Process each section
    for i, section in enumerate(sections[:4]):  # Limit to 4 sections
        # Clean narration text (remove markers)
        narration_text = f"{section['title']}. {section['content']}"
        narration_text = re.sub(r'\[.*?\]', '', narration_text)  # Remove any remaining brackets

        # Generate audio
        audio = text_to_speech(narration_text, f"section_{i}.mp3")
        if not audio:
            continue

        duration = max(MIN_SECTION_DURATION, audio.duration)
        color = SECTION_COLORS[i % len(SECTION_COLORS)]

        # Create slide with image support
        clip = create_section_slide(
            section['title'],
            section['content'],
            duration,
            color,
            section.get('image_keyword')
        ).set_start(current_time)

        clips.append(clip)
        audio_clips.append(audio.set_start(current_time))
        current_time += duration

    # Compose and render
    final_video = CompositeVideoClip(clips, size=VIDEO_SIZE)
    if audio_clips:
        final_video = final_video.set_audio(CompositeAudioClip(audio_clips))

    try:
        final_video.write_videofile(
            output_file,
            fps=FPS,
            codec='libx264',
            audio_codec='aac',
            preset='fast',
            threads=4
        )
        print(f"Video created: {output_file}")
        display_video(output_file)
    except Exception as e:
        print(f"Video rendering failed: {e}")


if __name__ == "__main__":
    topic = input("Enter a science topic: ").strip()
    if topic:
        generate_science_video(topic)
    else:
        print("Please enter a valid topic")