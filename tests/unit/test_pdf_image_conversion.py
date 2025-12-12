import unittest
import os
import base64
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from openlens_ai.utils.vision_feedback import get_fig_base64, convert_pdf_to_merged_image, convert_pdf_to_separate_images
from tests.utils.test_setup import setup_test_environment


class TestPdfConversion(unittest.TestCase):
    """Test PDF conversion functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_path, self.config_path = setup_test_environment("pdf_conversion")
        
        # Path to test PDF file
        self.test_pdf_path = os.path.join(self.test_path, "workspace", "manuscript", "example.pdf")
        

    def tearDown(self):
        """Clean up test environment"""
        # Clean up temporary directory
        
        # Commented out to preserve test artifacts for inspection
        # cleanup_test_environment(self.test_path)
        pass

    def test_get_fig_base64_with_pdf_merge(self):
        """Test get_fig_base64 function with PDF merge option"""
        if not os.path.exists(self.test_pdf_path):
            self.skipTest(f"Test PDF file not found at {self.test_pdf_path}")
        
        # Call get_fig_base64 with merge_pdf=True
        result = get_fig_base64([self.test_pdf_path], merge_pdf=True)
        
        # Verify the result
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)  # Should return one merged image
        
        # Verify the result structure
        name, img_base64 = result[0]
        self.assertIsInstance(name, str)
        self.assertIsInstance(img_base64, str)
        
        # Verify base64 data
        try:
            decoded_data = base64.b64decode(img_base64)
            self.assertGreater(len(decoded_data), 0)  # Should have some image data
        except Exception as e:
            self.fail(f"Invalid base64 data: {e}")

    def test_get_fig_base64_with_pdf_separate(self):
        """Test get_fig_base64 function with PDF separate pages option"""
        if not os.path.exists(self.test_pdf_path):
            self.skipTest(f"Test PDF file not found at {self.test_pdf_path}")
        
        # Call get_fig_base64 with merge_pdf=False (default)
        result = get_fig_base64([self.test_pdf_path], merge_pdf=False)
        
        # Verify the result
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)  # Should return at least one page
        
        # Verify the result structure for each page
        for name, img_base64 in result:
            self.assertIsInstance(name, str)
            self.assertIsInstance(img_base64, str)
            
            # Verify base64 data
            try:
                decoded_data = base64.b64decode(img_base64)
                self.assertGreater(len(decoded_data), 0)  # Should have some image data
            except Exception as e:
                self.fail(f"Invalid base64 data: {e}")

    def test_convert_pdf_to_merged_image(self):
        """Test convert_pdf_to_merged_image function directly"""
        # Call convert_pdf_to_merged_image
        save_path, img_base64 = convert_pdf_to_merged_image(self.test_pdf_path)
        
        # Verify the result
        self.assertIsNotNone(save_path)
        self.assertIsNotNone(img_base64)
        self.assertIsInstance(save_path, str)
        self.assertIsInstance(img_base64, str)
        
        # Verify base64 data
        try:
            decoded_data = base64.b64decode(img_base64)
            self.assertGreater(len(decoded_data), 0)  # Should have some image data
        except Exception as e:
            self.fail(f"Invalid base64 data: {e}")
        
        # Verify the saved file exists
        self.assertTrue(os.path.exists(save_path))

    def test_convert_pdf_to_separate_images(self):
        """Test convert_pdf_to_separate_images function directly"""
        # Call convert_pdf_to_separate_images
        name_list, img_base64_list = convert_pdf_to_separate_images(self.test_pdf_path)
        
        # Verify the result
        self.assertIsNotNone(name_list)
        self.assertIsNotNone(img_base64_list)
        self.assertIsInstance(name_list, list)
        self.assertIsInstance(img_base64_list, list)
        self.assertEqual(len(name_list), len(img_base64_list))
        self.assertGreater(len(name_list), 0)  # Should have at least one page
        
        # Verify each page
        for i, (name, img_base64) in enumerate(zip(name_list, img_base64_list)):
            self.assertIsInstance(name, str)
            self.assertIsInstance(img_base64, str)
            
            # Verify base64 data
            try:
                decoded_data = base64.b64decode(img_base64)
                self.assertGreater(len(decoded_data), 0)  # Should have some image data
            except Exception as e:
                self.fail(f"Invalid base64 data for page {i}: {e}")
            
            # Verify the saved file exists
            self.assertTrue(os.path.exists(name))


    def test_get_fig_base64_with_nonexistent_pdf(self):
        """Test get_fig_base64 function with nonexistent PDF"""
        nonexistent_pdf = "/path/to/nonexistent.pdf"
        
        # Call get_fig_base64 with nonexistent PDF
        result = get_fig_base64([nonexistent_pdf], merge_pdf=True)
        
        # Should return empty list for nonexistent file
        self.assertEqual(result, [])

    def test_get_fig_base64_with_empty_list(self):
        """Test get_fig_base64 function with empty file list"""
        # Call get_fig_base64 with empty list
        result = get_fig_base64([], merge_pdf=True)
        
        # Should return empty list
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()