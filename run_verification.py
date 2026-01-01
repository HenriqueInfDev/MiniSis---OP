import subprocess
import time
import os

def run_verification():
    """
    Launches the application in a virtual display, takes a screenshot,
    and then terminates the application.
    """
    display = ":99"
    xvfb_cmd = f"Xvfb {display} -screen 0 1280x1024x24"
    screenshot_path = "/home/jules/verification/verification.png"

    # Create the verification directory
    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)

    # Start the virtual display
    xvfb_proc = subprocess.Popen(xvfb_cmd.split())

    try:
        # Set environment variables for the application
        env = os.environ.copy()
        env["DISPLAY"] = display
        env["MINISIS_ENV"] = "test"

        # Launch the application
        app_proc = subprocess.Popen(["python", "main.py"], env=env)

        # Give the application time to start and render
        time.sleep(5)

        # Take the screenshot
        subprocess.run(["scrot", screenshot_path, "-d", "1"], env=env)

        # Terminate the application
        app_proc.terminate()
        app_proc.wait(timeout=5)

    finally:
        # Stop the virtual display
        xvfb_proc.terminate()
        xvfb_proc.wait(timeout=5)

if __name__ == "__main__":
    run_verification()
