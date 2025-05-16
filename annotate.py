from PIL import Image, ImageDraw, ImageFont
import json
import os

def draw_boxes_on_screenshot(screenshot_path, json_path, priority_path, output_path, box_width=200, box_height=30):
    # Load the screenshot
    img = Image.open(screenshot_path)
    draw = ImageDraw.Draw(img)

    # Load the JSON files
    with open(json_path, 'r', encoding='utf-8') as f:
        elements_data = json.load(f)
    
    with open(priority_path, 'r', encoding='utf-8') as f:
        priority_data = json.load(f)

    # Define a list of distinct colors for the boxes
    colors = [
        "red",
        "blue",
        "green",
        "purple",
        "orange",
        "cyan",
        "magenta",
        "yellow"
    ]

    for i, (element_key, _) in enumerate(priority_data.items()):
        # Convert element key to match the format in elements_data
        element_num = element_key.split()[-1]  # Get the number from "element X"
        element_id = f"ELEMENT {element_num}"
        
        if element_id in elements_data:
            element = elements_data[element_id]
            coords = element['Coordinates']
            
            if coords == 'null':
                continue  # Skip URL element

            # Parse coordinates
            coords = coords.strip('()')
            x, y = map(float, coords.split(','))

            # Draw rectangle with a different color for each element
            color = colors[i % len(colors)]  # Cycle through colors
            top_left = (x, y)
            bottom_right = (x + box_width, y + box_height)
            draw.rectangle([top_left, bottom_right], outline=color, width=3)

    img.save(output_path)
    print(f"✅ Output image with bounding boxes saved to {output_path}")

def generate_warning_html(screenshot_path, priority_path, output_html_path):
    # Load the priority data
    with open(priority_path, 'r', encoding='utf-8') as f:
        priority_data = json.load(f)

    # Define colors for the boxes
    colors = [
        "red",
        "blue",
        "green",
        "purple",
        "orange",
        "cyan",
        "magenta",
        "yellow"
    ]

    # Create the HTML content
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <title>⚠️ Warning: Website Detected as Phishing</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      background-color: #f8f9fa;
      margin: 0;
      padding: 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
    }}
    .container {{
      max-width: 1200px;
      width: 100%;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
      padding: 30px;
      margin-top: 20px;
    }}
    .warning-header {{
      color: #dc3545;
      font-size: 24px;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      width: 100%;
      text-align: center;
    }}
    .warning-icon {{
      width: 32px;
      height: 32px;
    }}
    .content-wrapper {{
      display: flex;
      gap: 30px;
      margin-top: 20px;
    }}
    .screenshot-section {{
      flex: 1;
      max-width: 50%;
      position: relative;
    }}
    .screenshot-section img {{
      width: 100%;
      border: 1px solid #dee2e6;
      border-radius: 4px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      transition: all 0.3s ease;
    }}
    .zoom-button {{
      position: absolute;
      bottom: 10px;
      right: 10px;
      background: rgba(0, 0, 0, 0.7);
      color: white;
      border: none;
      border-radius: 4px;
      padding: 8px 12px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 5px;
      font-size: 14px;
      z-index: 10;
    }}
    .zoom-button:hover {{
      background: rgba(0, 0, 0, 0.8);
    }}
    .fullscreen-overlay {{
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.9);
      z-index: 1000;
      justify-content: center;
      align-items: center;
    }}
    .fullscreen-image {{
      max-width: 90%;
      max-height: 90%;
      object-fit: contain;
    }}
    .close-button {{
      position: absolute;
      top: 20px;
      right: 20px;
      background: rgba(255, 255, 255, 0.2);
      color: white;
      border: none;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      font-size: 20px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .close-button:hover {{
      background: rgba(255, 255, 255, 0.3);
    }}
    .analysis-section {{
      flex: 1;
    }}
    .reason-section {{
      margin: 20px 0;
      padding: 15px;
      background-color: #f8f9fa;
    }}
    .reason-title {{
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 10px;
    }}
    .reason-details {{
      color: #6c757d;
      line-height: 1.6;
    }}
    .subtitle {{
      color: #495057;
      font-size: 20px;
      margin: 10px 0 30px 0;
      text-align: center;
      width: 100%;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="warning-header">
      ⚠️ WARNING: This Website Has Been Detected as Phishing
    </div>
    <div class="subtitle">Why is this website suspicious?</div>

    <div class="content-wrapper">
      <div class="screenshot-section">
        <img src="images/{os.path.basename(screenshot_path)}" alt="Annotated Screenshot" id="screenshot">
        <button class="zoom-button" onclick="showFullscreen()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>
          </svg>
          Zoom
        </button>
      </div>
      <div class="analysis-section">
"""

    # Add each reason section with matching colors
    for i, (element_key, data) in enumerate(priority_data.items()):
        color = colors[i % len(colors)]
        html_content += f"""
        <div class="reason-section" style="border-left: 4px solid {color};">
          <div class="reason-title" style="color: {color};">{data['feature_name']}</div>
          <div class="reason-details">{data['explanation']}</div>
        </div>
"""

    # Add the fullscreen overlay
    html_content += """
      </div>
    </div>
  </div>
  <div class="fullscreen-overlay" id="fullscreenOverlay">
    <button class="close-button" onclick="hideFullscreen()">×</button>
    <img src="images/{os.path.basename(screenshot_path)}" alt="Full Screenshot" class="fullscreen-image">
  </div>

  <script>
    function showFullscreen() {
      document.getElementById('fullscreenOverlay').style.display = 'flex';
      document.body.style.overflow = 'hidden';
    }

    function hideFullscreen() {
      document.getElementById('fullscreenOverlay').style.display = 'none';
      document.body.style.overflow = 'auto';
    }

    // Close fullscreen when clicking outside the image
    document.getElementById('fullscreenOverlay').addEventListener('click', function(e) {
      if (e.target === this) {
        hideFullscreen();
      }
    });
  </script>
</body>
</html>
"""

    # Write the HTML file
    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Warning HTML file saved to {output_html_path}")

if __name__ == "__main__":
    screenshot_path = "artifacts/website_screenshot.png"
    json_path = "artifacts/website_text_coordinates.json"
    priority_path = "artifacts/highest_priority_elements.json"
    output_path = "artifacts/website_screenshot_with_boxes.png"
    output_html_path = "artifacts/warning.html"

    draw_boxes_on_screenshot(screenshot_path, json_path, priority_path, output_path)
    generate_warning_html(output_path, priority_path, output_html_path)
