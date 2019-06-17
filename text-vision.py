from google.cloud import vision
from google.cloud.vision import types
import io
from PIL import Image, ImageDraw
from enum import Enum


image_file='/home/simran/opencv-text-recognition/images/0001.jpg'
image  = Image.open(image_file)

client = vision.ImageAnnotatorClient()
with io.open(image_file,'rb') as image_file1:
        content = image_file1.read()
content_image = types.Image(content=content)
response = client.document_text_detection(image=content_image)
document = response.full_text_annotation
i=0
res=[]
class FeatureType(Enum):
    PAGE = 1
    BLOCK = 2
    PARA = 3
    WORD = 4
    SYMBOL = 5


def draw_boxes(image, bounds, color,width=5):
    draw = ImageDraw.Draw(image)
    #orig=image.copy()
    global i
    for bound in bounds:
        draw.line([
            bound.vertices[0].x, bound.vertices[0].y,
            bound.vertices[1].x, bound.vertices[1].y,
            bound.vertices[2].x, bound.vertices[2].y,
            bound.vertices[3].x, bound.vertices[3].y,
            bound.vertices[0].x, bound.vertices[0].y],fill=color, width=width)
        startX=bound.vertices[0].x
        startY=bound.vertices[0].y
        endX=bound.vertices[2].x
        endY=bound.vertices[2].y
        dX = int((endX - startX) * 0.05)
        dY = int((endY - startY) * 0.05)

	# apply padding to each side of the bounding box, respectively
        startX = max(0, startX - dX)
        startY = max(0, startY - dY)
        endX = endX + (dX * 2)
        endY = endY + (dY * 2)
       # roi=orig[bound.vertices[0].x:bound.vertices[1].x,bound.vertices[0].y:bound.vertices[2].y]
       # crop=image.crop((startX,startY,endX,endY))
       # crop.save('/home/simran/test1.jpg')
        #res.append((text_within(document,startX,startY,endX,endY)))
        #i+=1
        #print("Block"+str(i)+res[i-1],)
        print(text_within(document,startX,startY,endX,endY))
        #results.append(((startX, startY, endX, endY), text))
   
    image.save('/home/simran/im2.jpg',)

def text_within(document,x1,y1,x2,y2): 
  text=""
  for page in document.pages:
    for block in page.blocks:
      for paragraph in block.paragraphs:
        for word in paragraph.words:
          for symbol in word.symbols:
            min_x=min(symbol.bounding_box.vertices[0].x,symbol.bounding_box.vertices[1].x,symbol.bounding_box.vertices[2].x,symbol.bounding_box.vertices[3].x)
            max_x=max(symbol.bounding_box.vertices[0].x,symbol.bounding_box.vertices[1].x,symbol.bounding_box.vertices[2].x,symbol.bounding_box.vertices[3].x)
            min_y=min(symbol.bounding_box.vertices[0].y,symbol.bounding_box.vertices[1].y,symbol.bounding_box.vertices[2].y,symbol.bounding_box.vertices[3].y)
            max_y=max(symbol.bounding_box.vertices[0].y,symbol.bounding_box.vertices[1].y,symbol.bounding_box.vertices[2].y,symbol.bounding_box.vertices[3].y)
            if(min_x >= x1 and max_x <= x2 and min_y >= y1 and max_y <= y2):
              text+=symbol.text
              if(symbol.property.detected_break.type==1 or 
                symbol.property.detected_break.type==3):
                text+=' '
              if(symbol.property.detected_break.type==2):
                text+='\t'
              if(symbol.property.detected_break.type==5):
                text+='\n'
    return text

def get_document_bounds(response, feature):
    bounds=[]
    for i,page in enumerate(document.pages):
        for block in page.blocks:
            if feature==FeatureType.BLOCK:
                bounds.append(block.bounding_box)
            for paragraph in block.paragraphs:
                if feature==FeatureType.PARA:
                    bounds.append(paragraph.bounding_box)
                for word in paragraph.words:
                    for symbol in word.symbols:
                        if (feature == FeatureType.SYMBOL):
                            bounds.append(symbol.bounding_box)
                    if (feature == FeatureType.WORD):
                        bounds.append(word.bounding_box)
    return bounds

def assemble_word(word):
    assembled_word=""
    for symbol in word.symbols:
        assembled_word+=symbol.text
    return assembled_word

def find_word_location(document,word_to_find):
    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    assembled_word=assemble_word(word)
                    if(assembled_word==word_to_find):
                        return word.bounding_box
                    
#location=find_word_location(document,'To')
#print(location)
bounds = get_document_bounds(response, FeatureType.BLOCK)
draw_boxes(image, bounds, 'red') 

