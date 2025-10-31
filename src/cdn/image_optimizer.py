"""Image optimization and WebP conversion service."""

import os
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
from config.settings import Config


class ImageOptimizer:
    """Service for optimizing and converting images for CDN delivery."""

    def __init__(self):
        self.enabled = Config.IMAGE_OPTIMIZATION_ENABLED
        self.webp_conversion = Config.IMAGE_WEBP_CONVERSION
        self.default_quality = Config.IMAGE_DEFAULT_QUALITY
        self.max_width = Config.IMAGE_MAX_WIDTH
        self.max_height = Config.IMAGE_MAX_HEIGHT

    def optimize_image(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        quality: Optional[int] = None,
        convert_to_webp: bool = True,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
    ) -> str:
        """
        Optimize an image and optionally convert to WebP.

        Args:
            input_path: Path to input image
            output_path: Path for output image (optional)
            quality: Image quality (1-100)
            convert_to_webp: Convert to WebP format
            max_width: Maximum width (will resize if larger)
            max_height: Maximum height (will resize if larger)

        Returns:
            Path to optimized image
        """
        if not self.enabled:
            return input_path

        # Open image
        img = Image.open(input_path)

        # Convert RGBA to RGB if saving as JPEG
        if img.mode == "RGBA" and not convert_to_webp:
            # Create white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
            img = background

        # Resize if needed
        width, height = img.size
        max_w = max_width or self.max_width
        max_h = max_height or self.max_height

        if width > max_w or height > max_h:
            img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

        # Determine output format and path
        if convert_to_webp and self.webp_conversion:
            format_ext = ".webp"
            save_format = "WEBP"
        else:
            format_ext = Path(input_path).suffix.lower()
            if format_ext in [".jpg", ".jpeg"]:
                save_format = "JPEG"
            elif format_ext == ".png":
                save_format = "PNG"
            elif format_ext == ".gif":
                save_format = "GIF"
            else:
                save_format = "JPEG"
                format_ext = ".jpg"

        # Determine output path
        if output_path is None:
            input_stem = Path(input_path).stem
            input_dir = Path(input_path).parent
            output_path = str(input_dir / f"{input_stem}_optimized{format_ext}")

        # Save optimized image
        save_quality = quality or self.default_quality
        save_kwargs = {"quality": save_quality, "optimize": True}

        if save_format == "WEBP":
            save_kwargs["method"] = 6  # Best compression
        elif save_format == "JPEG":
            save_kwargs["progressive"] = True

        img.save(output_path, format=save_format, **save_kwargs)

        return output_path

    def get_optimized_dimensions(
        self, width: int, height: int, max_width: Optional[int] = None, max_height: Optional[int] = None
    ) -> Tuple[int, int]:
        """
        Calculate optimized dimensions maintaining aspect ratio.

        Args:
            width: Original width
            height: Original height
            max_width: Maximum width
            max_height: Maximum height

        Returns:
            Tuple of (width, height)
        """
        max_w = max_width or self.max_width
        max_h = max_height or self.max_height

        if width <= max_w and height <= max_h:
            return (width, height)

        # Calculate scaling factor
        width_ratio = max_w / width
        height_ratio = max_h / height
        scale_factor = min(width_ratio, height_ratio)

        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)

        return (new_width, new_height)

    def batch_optimize(
        self,
        input_dir: str,
        output_dir: str,
        quality: Optional[int] = None,
        convert_to_webp: bool = True,
    ) -> list[str]:
        """
        Batch optimize all images in a directory.

        Args:
            input_dir: Directory containing images
            output_dir: Directory for optimized images
            quality: Image quality (1-100)
            convert_to_webp: Convert to WebP format

        Returns:
            List of optimized image paths
        """
        if not self.enabled:
            return []

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        optimized_images = []
        supported_formats = [".jpg", ".jpeg", ".png", ".gif", ".webp"]

        for filename in os.listdir(input_dir):
            file_path = os.path.join(input_dir, filename)
            if not os.path.isfile(file_path):
                continue

            ext = Path(filename).suffix.lower()
            if ext not in supported_formats:
                continue

            # Generate output path
            stem = Path(filename).stem
            output_ext = ".webp" if convert_to_webp and self.webp_conversion else ext
            output_path = os.path.join(output_dir, f"{stem}{output_ext}")

            try:
                optimized_path = self.optimize_image(
                    file_path, output_path, quality=quality, convert_to_webp=convert_to_webp
                )
                optimized_images.append(optimized_path)
            except Exception as e:
                print(f"Failed to optimize {filename}: {e}")

        return optimized_images

    def get_cdn_url(self, asset_path: str) -> str:
        """
        Get CDN URL for an asset.

        Args:
            asset_path: Relative path to asset

        Returns:
            Full CDN URL
        """
        if not Config.CDN_ENABLED or not Config.CDN_DOMAIN:
            return f"{Config.CDN_STATIC_ASSETS_URL}/{asset_path}"

        cdn_domain = Config.CDN_DOMAIN.rstrip("/")
        asset_path = asset_path.lstrip("/")

        return f"https://{cdn_domain}/{asset_path}"
