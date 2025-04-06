# moviepy_conf.py
from moviepy.config import change_settings
import os

# Set the path to ImageMagick - adjust this path to where you installed ImageMagick
# Typical path is C:\Program Files\ImageMagick-7.x.x-Q16-HDRI
# The exact version number will depend on what you installed
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})