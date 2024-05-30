import yaml
import cv2
import numpy as np


def quaternion_to_euler(x, y, z, w):

    import math
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    X = math.degrees(math.atan2(t0, t1))

    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    Y = math.degrees(math.asin(t2))

    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    Z = math.degrees(math.atan2(t3, t4))

    return Z




def add_point(map_image, circle_image, target_x, target_y, orientation, resolution, origin_x, origin_y, point_index):
    angle = np.rad2deg(quaternion_to_euler(0,0,orientation,1-orientation))
    
    image_height, image_width = map_image.shape[:2]
    # Convert the image to grayscale (if needed)
    # PGM is already grayscale but converting explicitly ensures consistency
    

    #Lines Calculate the origin of the robot correct to the image
    image_origin_x = int(-origin_x / resolution)
    image_origin_y = int(image_height + (origin_y / resolution))
    # Calculates the centre of the image;.
    image_x = int(((target_x/resolution) + image_origin_x) )
    image_y = int((-(target_y/resolution) + image_origin_y) )

    circle_image = cv2.resize(circle_image, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
    height, width = circle_image.shape[:2]
    if height % 2 != 0:
        height -= 1
    if width % 2 != 0:
        width -= 1
    # Crop the image to the new dimensions
    circle_image = circle_image[:height, :width]
    circle_image_height, circle_image_width = circle_image.shape[:2]
    # Calculate the center of the image
    center = (circle_image_width // 2, circle_image_height // 2)
    circle_center_y = circle_image_height // 2
    circle_center_x = circle_image_width // 2
    flag = True
    #Gets the region the circle will be placed in the map image
    while ((image_y-circle_center_y < 0) or (image_y+circle_center_y > image_height) or (image_x-circle_center_x < 0) or (image_x+circle_center_x > image_width)):
        if image_y-circle_center_y < 0:
            image_y += 1
            flag = False
        if image_y+circle_center_y > image_height:
            image_y -= 1
            flag = True
        if image_x-circle_center_x < 0:
            image_x += 1
        if image_x+circle_center_x > image_width:
            image_x -= 1

       
    # Get the rotation matrix
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    
    # Perform the rotation
    rotated_circle_image = cv2.warpAffine(circle_image, rotation_matrix, (circle_image_width+20, circle_image_height+20))
    circle_image_height, circle_image_width = rotated_circle_image.shape[:2]
    # Calculate the center of the image
    center = (circle_image_width // 2, circle_image_height // 2)
    circle_center_y = circle_image_height // 2
    circle_center_x = circle_image_width // 2
    roi = map_image[image_y-circle_center_y:image_y+circle_center_y, image_x-circle_center_x:image_x+circle_center_x] 
    #cv2.imshow("Rotated Image", rotated_circle_image)
    #cv2.waitKey(0)
    hsv_circle_image = cv2.cvtColor(rotated_circle_image, cv2.COLOR_BGR2HSV)
    # Define range for red color in HSV
    lower_red = np.array([0, 70, 50])
    upper_red = np.array([10, 255, 255])
    # Create a mask to isolate red parts of the image
    mask = cv2.inRange(hsv_circle_image, lower_red, upper_red)

    # Bitwise-AND mask and circle_image
    red_part = cv2.bitwise_and(rotated_circle_image, rotated_circle_image, mask=mask)
    red_part = cv2.cvtColor(red_part, cv2.COLOR_BGR2BGRA)
    #cv2.imshow("Your Image",red_part)
    #cv2.waitKey(0)
    red_pixels_mask = np.all(red_part[:, :, :3] == [0, 0, 255], axis=-1)

    # Set the alpha channel of the red pixels to 255
    red_part[red_pixels_mask, 3] = 255

    roi3 = cv2.cvtColor(roi, cv2.COLOR_BGR2BGRA)
    mask = mask.astype(bool)

    roi3[mask] = red_part[mask]

    # Convert the grayscale image to RGBA
# Convert the grayscale image to BGRA if it's not already
    if map_image.shape[2] != 4:
        map_image = cv2.cvtColor(map_image, cv2.COLOR_BGR2BGRA)

    map_image[image_y-circle_center_y:image_y+circle_center_y, image_x-circle_center_x:image_x+circle_center_x] = roi3

    # Adds the Point number to the image
    text = f"MP{point_index+1}"
    # Define the position for the text
    if flag == True:
        position = (image_x, image_y-circle_center_y-10)  # (x, y)
    else:
        position = (image_x, image_y+circle_center_y+10)

    # Define the font
    font = cv2.FONT_HERSHEY_SIMPLEX
    # Define the font size
    font_scale = 0.75
    # Define the color for the text (B, G, R)
    color = (0, 0, 255)  # white
    # Define the line thickness
    thickness = 2
    # Add the text to the image
    cv2.putText(map_image, text, position, font, font_scale, color, thickness)

    return map_image



def main():
    file = 'substation.pgm'
    filen = "HVLab4"
    target_x = 26.8
    target_y = -3.74
    orientation = 0.1
    prefix = "HV_monitoring/maps/"
    # Read YAML file data
    with open(f"{prefix}{filen}.yaml") as f:
        map_data = yaml.safe_load(f)
    with open(f"HV_monitoring/route.yaml", "r") as f:
        points = yaml.safe_load(f)

    points_list = [[point["x"], point["y"], point["z"]] for point in points.values() if isinstance(point, dict) and "x" in point and "y" in point and "z" in point]
    # Combine x, y, z values into a list

    # Extract resolution and origin
    resolution = map_data["resolution"]
    origin_x = map_data["origin"][0] 
    origin_y = map_data["origin"][1]

    resolution = resolution /2
    

    # Read the image using cv2.imread() with the -1 flag for unchanged format
    image = cv2.imread(f"{prefix}{filen}.pgm", 0)
    circle_image = cv2.imread("Mp2.png", cv2.IMREAD_UNCHANGED)
    if image is None or circle_image is None:
        print("Error opening image:", filen)
        exit()
    image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_AREA)
    image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    
    for point_index, pt in enumerate(points_list):
        try:
            image = add_point(image, circle_image, pt[0], pt[1], pt[2], resolution, origin_x, origin_y, point_index)
        except Exception as e:
            print(f"Unable to process point {pt[0]},{pt[1]}: {e}")

    # Check if image reading was successful
    
    # Display the image using cv2.imshow(
    
    cv2.imshow("Your Image", image)
    cv2.waitKey(0)
    cv2.imwrite(f"{filen}.png", image)
    # Close all open windows
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()