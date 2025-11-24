import os
import sys
import base64
sys.path.append('/data/cyx/openlens-ai')

from openlens_ai.utils.vision_feedback import get_fig_base64

# Test with a sample PDF if it exists
pdf_path = "/data/cyx/openlens-ai/outputs/power_grid_fault_id_20251121164412/workspace/manuscript/main.pdf"

if os.path.exists(pdf_path):
    print(f"Testing PDF conversion with: {pdf_path}")
    try:
        result = get_fig_base64([pdf_path], merge_pdf=True)
        print(f"Conversion successful! Generated {len(result)} images.")
        for name, img_data in result:
            print(f"  - {name}")
            # Save the base64 image data to a file
            output_path = name  # Use the full path returned from get_fig_base64
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(img_data))
            print(f"    Saved to: {output_path}")
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        import traceback
        traceback.print_exc()
else:
    print(f"PDF file not found at: {pdf_path}")
    print("Please provide a valid PDF path for testing.")