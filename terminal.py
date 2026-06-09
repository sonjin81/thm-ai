import subprocess, socket, fcntl, struct, os
from PIL import Image, ImageDraw, ImageFont

def save_output_as_image(text, filename):
    os.makedirs("writeups/images", exist_ok=True)
    img = Image.new('RGB', (950, 650), color=(15, 15, 15))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
    except:
        font = ImageFont.load_default()

    display_text = text[:3500] 
    d.text((20, 20), display_text, fill=(0, 255, 65), font=font)
    img.save(f"writeups/images/{filename}.png")

def execute_command(command, step_num):
    print(f"\n>>> [Execute Step {step_num}]: {command}")
    try:
        process = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=300,
            env=os.environ.copy()
        )
        output = f"$ {command}\n\n{process.stdout}{process.stderr}"
        save_output_as_image(output, f"step_{step_num}_output")
        return output
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        save_output_as_image(error_msg, f"step_{step_num}_output")
        return error_msg

def get_vpn_ip(ifname='tun0'):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(), 0x8915, struct.pack('256s', ifname[:15].encode('utf-8'))
        )[20:24])
    except:
        return "127.0.0.1"
