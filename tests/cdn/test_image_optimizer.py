"""Tests for image optimization functionality."""

import os
import tempfile
import pytest
from PIL import Image
from src.cdn.image_optimizer import ImageOptimizer


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_image(temp_dir):
    """Create a sample test image."""
    img_path = os.path.join(temp_dir, "test_image.jpg")
    # Create a 1000x1000 RGB image
    img = Image.new("RGB", (1000, 1000), color=(73, 109, 137))
    img.save(img_path, "JPEG")
    return img_path


@pytest.fixture
def sample_png_image(temp_dir):
    """Create a sample PNG test image with transparency."""
    img_path = os.path.join(temp_dir, "test_image.png")
    # Create a 1000x1000 RGBA image
    img = Image.new("RGBA", (1000, 1000), color=(73, 109, 137, 200))
    img.save(img_path, "PNG")
    return img_path


class TestImageOptimizer:
    """Test cases for ImageOptimizer class."""

    def test_init(self):
        """Test ImageOptimizer initialization."""
        optimizer = ImageOptimizer()
        assert optimizer is not None
        assert optimizer.default_quality == 85
        assert optimizer.max_width == 2048
        assert optimizer.max_height == 2048

    def test_optimize_image_basic(self, sample_image, temp_dir):
        """Test basic image optimization."""
        optimizer = ImageOptimizer()
        output_path = os.path.join(temp_dir, "optimized.jpg")
        
        result = optimizer.optimize_image(
            sample_image,
            output_path=output_path,
            convert_to_webp=False
        )
        
        assert os.path.exists(result)
        assert result == output_path
        
        # Check file size is reduced
        original_size = os.path.getsize(sample_image)
        optimized_size = os.path.getsize(result)
        assert optimized_size <= original_size

    def test_optimize_image_webp_conversion(self, sample_image, temp_dir):
        """Test WebP conversion."""
        optimizer = ImageOptimizer()
        output_path = os.path.join(temp_dir, "optimized.webp")
        
        result = optimizer.optimize_image(
            sample_image,
            output_path=output_path,
            convert_to_webp=True
        )
        
        assert os.path.exists(result)
        assert result.endswith(".webp")
        
        # Verify it's a valid WebP image
        img = Image.open(result)
        assert img.format == "WEBP"

    def test_optimize_image_resize(self, sample_image, temp_dir):
        """Test image resizing."""
        optimizer = ImageOptimizer()
        output_path = os.path.join(temp_dir, "resized.jpg")
        
        result = optimizer.optimize_image(
            sample_image,
            output_path=output_path,
            max_width=500,
            max_height=500,
            convert_to_webp=False
        )
        
        # Check dimensions
        img = Image.open(result)
        width, height = img.size
        assert width <= 500
        assert height <= 500

    def test_optimize_image_quality(self, sample_image, temp_dir):
        """Test quality parameter."""
        optimizer = ImageOptimizer()
        
        # High quality
        high_quality = os.path.join(temp_dir, "high_quality.jpg")
        optimizer.optimize_image(
            sample_image,
            output_path=high_quality,
            quality=95,
            convert_to_webp=False
        )
        
        # Low quality
        low_quality = os.path.join(temp_dir, "low_quality.jpg")
        optimizer.optimize_image(
            sample_image,
            output_path=low_quality,
            quality=50,
            convert_to_webp=False
        )
        
        # High quality should have larger file size
        high_size = os.path.getsize(high_quality)
        low_size = os.path.getsize(low_quality)
        assert high_size > low_size

    def test_optimize_png_to_jpg(self, sample_png_image, temp_dir):
        """Test PNG to JPEG conversion."""
        optimizer = ImageOptimizer()
        output_path = os.path.join(temp_dir, "converted.jpg")
        
        result = optimizer.optimize_image(
            sample_png_image,
            output_path=output_path,
            convert_to_webp=False
        )
        
        # Verify conversion
        img = Image.open(result)
        assert img.format == "JPEG"
        assert img.mode == "RGB"  # No alpha channel

    def test_get_optimized_dimensions(self):
        """Test dimension calculation."""
        optimizer = ImageOptimizer()
        
        # No resize needed
        width, height = optimizer.get_optimized_dimensions(800, 600)
        assert width == 800
        assert height == 600
        
        # Width exceeds max
        width, height = optimizer.get_optimized_dimensions(3000, 2000, max_width=1000, max_height=1000)
        assert width == 1000
        assert height == 666  # Maintains aspect ratio (int rounding)
        
        # Height exceeds max
        width, height = optimizer.get_optimized_dimensions(800, 1500, max_width=1000, max_height=1000)
        assert width == 533
        assert height == 1000

    def test_batch_optimize(self, temp_dir):
        """Test batch optimization."""
        # Create multiple test images
        input_dir = os.path.join(temp_dir, "input")
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(input_dir)
        
        for i in range(3):
            img = Image.new("RGB", (500, 500), color=(i * 50, i * 50, i * 50))
            img.save(os.path.join(input_dir, f"test_{i}.jpg"), "JPEG")
        
        optimizer = ImageOptimizer()
        results = optimizer.batch_optimize(input_dir, output_dir, convert_to_webp=False)
        
        assert len(results) == 3
        assert os.path.exists(output_dir)
        assert len(os.listdir(output_dir)) == 3

    def test_get_cdn_url(self, monkeypatch):
        """Test CDN URL generation."""
        # Test without CDN
        monkeypatch.setattr("config.settings.Config.CDN_ENABLED", False)
        monkeypatch.setattr("config.settings.Config.CDN_STATIC_ASSETS_URL", "/static")
        
        optimizer = ImageOptimizer()
        url = optimizer.get_cdn_url("images/logo.png")
        assert url == "/static/images/logo.png"
        
        # Test with CDN
        monkeypatch.setattr("config.settings.Config.CDN_ENABLED", True)
        monkeypatch.setattr("config.settings.Config.CDN_DOMAIN", "cdn.soundhash.io")
        
        url = optimizer.get_cdn_url("images/logo.png")
        assert url == "https://cdn.soundhash.io/images/logo.png"

    def test_optimize_image_auto_output_path(self, sample_image, temp_dir):
        """Test automatic output path generation."""
        optimizer = ImageOptimizer()
        
        # Without explicit output path
        result = optimizer.optimize_image(sample_image, convert_to_webp=False)
        
        assert os.path.exists(result)
        assert "_optimized" in result
        
        # Clean up
        if os.path.exists(result):
            os.remove(result)

    def test_disabled_optimization(self, sample_image, monkeypatch):
        """Test behavior when optimization is disabled."""
        monkeypatch.setattr("config.settings.Config.IMAGE_OPTIMIZATION_ENABLED", False)
        
        optimizer = ImageOptimizer()
        result = optimizer.optimize_image(sample_image)
        
        # Should return original path unchanged
        assert result == sample_image

    def test_batch_optimize_disabled(self, temp_dir, monkeypatch):
        """Test batch optimization when disabled."""
        monkeypatch.setattr("config.settings.Config.IMAGE_OPTIMIZATION_ENABLED", False)
        
        optimizer = ImageOptimizer()
        results = optimizer.batch_optimize(temp_dir, temp_dir)
        
        assert results == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
