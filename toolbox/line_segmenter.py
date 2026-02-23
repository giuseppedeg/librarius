import torch
from torchvision import transforms
from torchvision.utils import save_image
from .line_segmenter_model import UNetMini
from PIL import Image, ImageFilter, ImageDraw
from PIL.ImageOps import invert
from scipy.signal import find_peaks
import numpy
import os
import utils

IMG_SIZE = (800,800)

th_r = 150
th_g = 150
th_mask = 220
mask_type = "R"


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def compute_seg_mask(checkpoint_ls, image_path, out_imgs_dir="."):
    if not os.path.exists(out_imgs_dir):
        os.mkdir(out_imgs_dir)

    img_name = os.path.splitext(os.path.basename(image_path))[0]
    out_mask_path = os.path.join(out_imgs_dir, f"{img_name}.png")

    model = UNetMini(num_classes=3, in_channels=3)
    model.to(device)

    checkpoint_load = torch.load(checkpoint_ls, map_location=device)
    model.load_state_dict(checkpoint_load['model'])
    modelname = checkpoint_load['name']

    image = Image.open(image_path)
    image.convert("RGB")

    transform = transforms.Compose([
        transforms.Resize(IMG_SIZE),
        transforms.ToTensor()
    ])

    model.eval()
    with torch.no_grad():
        image = transform(image)
        image = image.to(device)
        image = image.unsqueeze(0)
        output = model(image)
        output = output.squeeze()
        save_image(output.cpu(), out_mask_path)
    
    mask_img = Image.open(out_mask_path)

    np_pred_m = numpy.array(mask_img)

    R_pred_m = np_pred_m[:,:,0]
    G_pred_m = np_pred_m[:,:,1]
    B_pred_m = np_pred_m[:,:,2]

    R_pred_m[R_pred_m >= th_r] = 255
    R_pred_m[R_pred_m < th_r] = 0

    G_pred_m[G_pred_m >= th_g] = 255
    G_pred_m[G_pred_m < th_g] = 0

    if mask_type == "R":
        mask = R_pred_m
    elif mask_type == "G":
        mask = G_pred_m
    else:
        mask = R_pred_m + G_pred_m
        mask[mask >= 255] = 255
        
    mask = Image.fromarray(mask)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=3))
    mask = invert(mask)
    mask = mask.point( lambda p: 255 if p > th_mask else 0 )

    mask.save(out_mask_path)


def line_segm(img_orig_path, img_mask_path, out_segfile_dir=".", margin=(0,0,0,0)):
    img = Image.open(img_mask_path)
    orig_img = Image.open(img_orig_path)
    img_draw = ImageDraw.Draw(img) 

    image_name = os.path.basename(img_orig_path)

    border_margin = int(img.size[1]*0.03)

    img_draw.line((0,(border_margin/2)-1, img.size[0],border_margin/2-1), fill=255, width=border_margin)
    img_draw.line((0,img.size[1]+1-border_margin/2, img.size[0],img.size[1]+1-border_margin/2), fill=255, width=border_margin)
    img_draw.line(((border_margin/2)-1,0, (border_margin/2)-1,img.size[1]), fill=255, width=border_margin)
    img_draw.line((img.size[0]+1-border_margin/2,0, img.size[0]+1-border_margin/2,img.size[1]), fill=255, width=border_margin)
    
    im_invert = invert(img.convert('L'))

    H_proj = utils.horizontal_projections(im_invert)
    
    threshold = (numpy.max(H_proj)-numpy.min(H_proj))*0.25
    distance = H_proj.shape[0]*0.02
    # prominence = (len(hpp))/PROMINANCE_PK#n_rows

    all_peaks_ind, _ = find_peaks(H_proj, height=threshold, distance=distance, prominence=100)

    # COMPUTE VERTICAL BOUNDARIES
    cutting_bounds = []
    prev_bound = 0

    for ind, peak in enumerate(all_peaks_ind):
        if ind < len(all_peaks_ind)-1:
            bound = int(peak + ((all_peaks_ind[ind+1]-peak) / 2))
            cutting_bounds.append((prev_bound,bound))
            prev_bound = bound
        else:
            cutting_bounds.append((prev_bound,img.size[1]))

    lines_masksize = [] # left, upper, right, lower

    # REFINE BORDERS SHRINKING THE LINE
    for ind, line in enumerate(cutting_bounds):
        line_img = img.crop((0, line[0], img.size[0], line[1]))
        line_img_inv = invert(line_img.convert('L'))
        # left, upper, right, lower

        H_proj_line = utils.horizontal_projections(line_img_inv)
        V_proj_line = utils.vertical_projections(line_img_inv)
        
        peak_h = max(H_proj_line)
        y_center = numpy.where(H_proj_line == peak_h)[0][0]
        
        y0 = y_center
        H_value = H_proj_line[y0]
        while H_value != 0 and y0 > 0:
            y0 -= 1
            H_value = H_proj_line[y0]

        y1 = y_center
        H_value = H_proj_line[y1]
        while H_value != 0 and y1 < line_img.size[1]-1:
            y1 += 1
            H_value = H_proj_line[y1]

        x0 = 0
        V_value = V_proj_line[x0]
        while V_value == 0 and x0 < line_img.size[0]:
            x0 += 1
            V_value = V_proj_line[x0]
        
        x1 = line_img.size[0]
        V_value = V_proj_line[x1-1]
        while V_value == 0 and x1 > 1:
            x1 -= 1
            V_value = V_proj_line[x1-1]
        
        lines_masksize.append((x0-margin[0], 
                                line[0]+y0-margin[1],
                                x1+margin[2], 
                                line[1]-line_img.size[1]+y1+margin[3])) # left, upper, right, lower


    #RESIZE LINES TO ORIGINAL IMAGE SIZE
    orig_w, orig_h = orig_img.size
    mask_w, mask_h = img.size
    w_factor = orig_w/mask_w
    h_factor = orig_h/mask_h
    lines_imagesize = []

    for line in lines_masksize:
        resized_line = (int(line[0]*w_factor), int(line[1]*h_factor), int(line[2]*w_factor), int(line[3]*h_factor))
        lines_imagesize.append(resized_line)

    # SAVE SEGMENTATION FILE
    edit_img = orig_img.copy()
    draw = ImageDraw.Draw(edit_img)  
    with open(os.path.join(out_segfile_dir, os.path.splitext(image_name)[0]), "w") as out_file:
        out_file.write("id_line,x,y,w,h\n")

        for id, line in enumerate(lines_imagesize):
            id_line = str(id).zfill(4)
            out_file.write(f"{id_line},{line[0]},{line[1]},{line[2]-line[0]},{line[3]-line[1]}\n")


if __name__ == "__main__":
    CHECKPOINT_L_SEGMENTER = "models\\line_segmenter\\0195.pth"
    margin_lines = (20,0,20,10)

    img = "data\\doc_img\\001.jpg"
    compute_seg_mask(CHECKPOINT_L_SEGMENTER, img)

    line_segm(img, "001.png", ".", margin=margin_lines)

    print("Done")