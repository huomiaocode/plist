#!python
import os
from optparse import OptionParser
from xml.etree import ElementTree
from PIL import Image


def tree_to_obj(tree):
    obj = {}
    for index, item in enumerate(tree):
        if item.tag == 'key':
            if tree[index+1].tag == 'string':
                obj[item.text] = tree[index+1].text
            elif tree[index+1].tag == 'true':
                obj[item.text]=True
            elif tree[index+1].tag == 'false':
                obj[item.text]=False
            elif  tree[index+1].tag == "integer":
                obj[item.text]=tree[index+1].text
            elif  tree[index+1].tag == "array":
                obj[item.text]=tree[index+1].text
            elif tree[index+1].tag == 'dict':
                obj[item.text] = tree_to_obj(tree[index+1])
    return obj

def to_list(x):
    return x.replace('{','').replace('}','').split(',')

def gen_image_0(big_image, frame_obj):
    x = int(frame_obj['x'])
    y = int(frame_obj['y'])
    width = int(frame_obj['width'])
    height = int(frame_obj['height'])
    box = (
        int(x),
        int(y),
        int(x + width),
        int(y + height)
    )
    rect_on_big = big_image.crop(box)
    return rect_on_big

def gen_image_1_2(big_image, frame_obj):
    rectlist = to_list(frame_obj['frame'])
    width = int(rectlist[3] if frame_obj['rotated'] else rectlist[2])
    height = int(rectlist[2] if frame_obj['rotated'] else rectlist[3])
    box = (
        int(rectlist[0]),
        int(rectlist[1]),
        int(rectlist[0])+width,
        int(rectlist[1])+height,
    )
    sizelist = [int(x)for x in to_list(frame_obj['sourceSize'])]
    rect_on_big = big_image.crop(box)
    if frame_obj['rotated']:
        rect_on_big = rect_on_big.transpose(Image.ROTATE_90)
    result_image = Image.new('RGBA',sizelist,(0,0,0,0))
    offset = [int(x)for x in to_list(frame_obj['offset'])]
    if frame_obj['rotated']:
        result_box=(
            (sizelist[0] - height) / 2 + offset[0],
            (sizelist[1] - width) / 2 + offset[1],
        )
    else:
        result_box=(
            (sizelist[0] - width)/2 + offset[0],
            (sizelist[1] - height)/2 + offset[1]
        )
    
    result_image.paste(rect_on_big,result_box)
    return result_image

def gen_image_3(big_image, frame_obj):
    rectlist = to_list(frame_obj['textureRect'])
    width = int(rectlist[3] if frame_obj['textureRotated'] else rectlist[2])
    height = int(rectlist[2] if frame_obj['textureRotated'] else rectlist[3])
    box = (
        int(rectlist[0]),
        int(rectlist[1]),
        int(rectlist[0]) + width,
        int(rectlist[1]) + height,
    )
    sizelist = [int(x)for x in to_list(frame_obj['spriteSize'])]
    rect_on_big = big_image.crop(box)
    if frame_obj['textureRotated']:
        rect_on_big = rect_on_big.transpose(Image.ROTATE_90)
    result_image = Image.new('RGBA',sizelist,(0,0,0,0))
    offset = [float(x)for x in to_list(frame_obj['spriteOffset'])]
    orsize = [int(x)for x in to_list(frame_obj['spriteSourceSize'])]
    width = orsize[0]
    height = orsize[1]
    result_box=(
        int(offset[0]),
        int(offset[1])
    )

    result_image.paste(rect_on_big, result_box)
    return result_image

def gen_png(plist_file, png_file, output_path = None):
    print("gen_png start")

    print("plist_file = %s" % plist_file)
    print("png_file = %s" % png_file)

    plist_content = ""
    with open(plist_file, "r") as f:
        plist_content = f.read()
    root = ElementTree.fromstring(plist_content)
    plist_obj = tree_to_obj(root[0])

    png_path, png_name = os.path.split(png_file)
    png_name, _ = os.path.splitext(png_name)
    
    if output_path == None:
        output_path = os.path.join(png_path, png_name)

    print("output_path is %s" % output_path)

    # create path
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    png_image = Image.open(png_file)
    result_image = None

    format = None
    if plist_obj.has_key("metadata") and plist_obj["metadata"].has_key("format"):
        format = int(plist_obj["metadata"]["format"])

    print("gen_png format = %s" % format)
    
    for p_name, frame_obj in plist_obj['frames'].items():
        if format == 0:
            result_image = gen_image_0(png_image, frame_obj)
        elif format == 1 or format == 2:
            result_image = gen_image_1_2(png_image, frame_obj)
        elif format == 3:
            result_image = gen_image_3(png_image, frame_obj)

        if result_image != None:
            to_file = os.path.join(output_path, p_name)
            print("save %s" % to_file)
            result_image.save(to_file)

    print("gen_png end")

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-p", "--plist", dest="plist", help="plist file")
    parser.add_option("-o", "--output", dest="output", help="output path")
    (options, args) = parser.parse_args()

    if options.plist != None:
        file_name, _ = os.path.splitext(options.plist)
        plist_filename = file_name + '.plist'
        png_filename = file_name + '.png'
        gen_png(plist_filename, png_filename, options.output)
