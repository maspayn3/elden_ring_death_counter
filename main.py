import cv2
import os
import numpy as np
import time
from mss import mss
from datetime import datetime

# === ER DEATH COUNTER ===
# Run this script in the background while you are playing Elden Ring
# and it will automatically count and store the number of times you die.
# 
# Will be customized to include co-op player deaths

def read_death_count():
    """Read total current death count from file"""
    death_count_file = "death_count.txt"
    if os.path.exists(death_count_file):
        with open(death_count_file, "r") as file:
            try:
                return int(file.read().strip())
            except ValueError:
                print("Error: Could not read death count file")
                return 0
    else:
        print("Error: Could not find death_count.txt")        
    
    return 0


def write_death_count(death_count):
    """Write the updated death count to the file."""
    death_count_file = "death_count.txt"
    with open(death_count_file, "w") as file:
        file.write(str(death_count))


def enhance_red(image):
    # Check if the image is RGBA (4 channels) or BGR (3 channels)
    if image.shape[2] == 4:
        # For RGBA images (screenshots)
        b, g, r, a = cv2.split(image)
        bgr = cv2.merge([b, g, r])
    else:
        # For BGR images (template)
        bgr = image

    # Convert to HSV
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    
    # Define range for red color
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    
    # Create masks for red regions
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = mask1 + mask2
    
    # Create a red image
    red_img = np.zeros_like(bgr)
    red_img[mask > 0] = [0, 0, 255]
    
    # Blend with original image
    result = cv2.addWeighted(bgr, 1, red_img, 0.5, 0)
    
    return result


def capture_screen(monitor):
    # necessary to convert to np.array() due to OpenCV workign w/ arrays
    with mss() as sct:
        screenshot = np.array(sct.grab(monitor))
        return screenshot
    

def detect_you_died(image, template, threshold=0.6):
    # Attempts to find area in image similar to my template
    #   -> cv2.TM_CCOEFF_NORMED -> normalized correlation coefficient 
    #   - scale invariant: works well even if brightness is a mismatch
    #   - gives normalized range [-1, 1] where 1 is a perfect match
    # Ensure the image is in the correct format
    try:
        # DEBUG to ensure processing worked
        # save_processed_image(image, template, 0)

        # Perform template matching
        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val > threshold:
            return True, max_loc, (max_loc[0] + template.shape[1], max_loc[1] + template.shape[0]), max_val
        return False, None, None, max_val
    
    except Exception as e:
        print(f"Error in detect_you_died: {e}")
        return False, None, None, None


def save_death_screenshot(screenshot, death_count, top_left, bottom_right):
    if not os.path.exists("you_died_screenshots"):
        os.makedirs("you_died_screenshots")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"death_screenshots/death_{death_count}_{timestamp}.png"
    
    color_screenshot = screenshot.copy()

    # Put debug rectangle and death number information 
    cv2.rectangle(color_screenshot, top_left, bottom_right, (0, 255, 0), 2)
    cv2.putText(color_screenshot, f"Death #{death_count}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Save the image
    cv2.imwrite(filename, color_screenshot)
    print(f"Death screenshot saved: {filename}")


def debug_template_match(screenshot, template, death_count, match_value, top_left, bottom_right):
    """Debug function used to verify template image processing and matching worked"""
    debug_img = screenshot.copy()

    if top_left and bottom_right:
        cv2.rectangle(debug_img, top_left, bottom_right, (0, 255, 0), 2)
    
    cv2.putText(debug_img, f"Match: {match_value:.2f}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    if not os.path.exists("debug_screenshots"):
        os.makedirs("debug_screenshots")

    filename = f"debug_screenshots/debug_{death_count}.png"
    cv2.imwrite(filename, debug_img)


def save_processed_image(image, template, death_count):
    if not os.path.exists("processed_images"):
        os.makedirs("processed_images")
    
    # Save screenshot
    cv2.imwrite(f"processed_images/processed_screenshot_{death_count}.png", image)
    
    # Save template
    cv2.imwrite(f"processed_images/processed_template_{death_count}.png", template)
    
    # Save the original screenshots's red channel for comparison
    red_channel = image[:,:,2]
    cv2.imwrite(f"processed_images/original_red_channel_{death_count}.png", red_channel)

    print(f"Processed images saved for iteration {death_count}")
    

def main():
    # Define the screen region to capture (adjust as needed)
    monitor = {"top": 0, "left": 0, "width": 3840, "height": 2160}
    template_path = 'template.jpg'

    if not os.path.exists(template_path):
        print(f"Error: Template image '{template_path}' not found.")
        print("Please ensure you have a screenshot of the 'YOU DIED' text from Elden Ring")
        print("saved as 'template.png' in the same directory as this script.")
        return
    
    # Convert template to grayscale upon read
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    template = enhance_red(template)
    print(f"Template shape: {template.shape}")

    if template is None:
        print(f"Error: Failed to load template image '{template_path}'.")
        print("Please ensure the image file is not corrupted.")
        return
    
    death_count = read_death_count()

    print("Elden Ring Death Counter started.")
    print("Monitoring for deaths... (Ctrl+C to stop)")

    try:
        while True:
            # Capture the screen
            screenshot = capture_screen(monitor)
            screenshot = enhance_red(screenshot)
            # save_processed_image(screenshot, template, death_count)

            # Check for "YOU DIED" text
            detected, top_left, bottom_right, match_val  = detect_you_died(screenshot, template)
            # debug_template_match(screenshot, template, death_count, match_val, top_left, bottom_right)

            if detected:
                death_count += 1
                print(f"Death detected! Count: {death_count}")
                save_death_screenshot(screenshot, death_count, top_left, bottom_right)
                time.sleep(5)

            # "You died appears for around 2 seconds, leaving us time to pause"
            time.sleep(1.5)

    except KeyboardInterrupt:
        print(f"\nScript stopped. Final death count: {death_count}")
        write_death_count(death_count)
        print(f"Death count saved to death_count.txt.")

    except Exception as e:
        print(f"An error has occurred: {e}")

    finally:
        print("Thank you for using the Elden Ring Death Counter")


if __name__ == "__main__":
    main()