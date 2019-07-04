from google.cloud import vision
from google.cloud.vision import types
import io
from PIL import Image, ImageDraw
from enum import Enum
import json
import argparse
import re
from pdf2image import convert_from_path
import glob


i=0
j=0
res=[]
block=[]
output={}
class FeatureType(Enum):
    PAGE = 1
    BLOCK = 2
    PARA = 3
    WORD = 4
    SYMBOL = 5

#Gives bounding vertices of required type- block,paragraph,word,symbol
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

#Vertices of each word is recorded.
def draw_boxes(image, bounds):
    #orig=image.copy()
    global i
    for bound in bounds:
        startX=bound.vertices[0].x
        startY=bound.vertices[0].y
        endX=bound.vertices[2].x
        endY=bound.vertices[2].y
        res.append((startX,startY,endX,endY,text_within(document,startX,startY,endX,endY)))
        i+=1
    #Sorting result top to bottom, left to right
    res.sort(key = lambda x: (x[1],x[0]))
    return(res)

#Vertices of each block is recorded 
def draw_blocks(image,bounds):
  global j
  for bound in bounds:
    startX=bound.vertices[0].x
    startY=bound.vertices[0].y
    endX=bound.vertices[2].x
    endY=bound.vertices[2].y
    block.append((startX,startY,endX,endY,text_within(document,startX,startY,endX,endY)))
    j+=1
  block.sort(key = lambda x: (x[1],x[0]))
  return(block)

#Finding Text within set bounding box
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
              if(symbol.property.detected_break.type==1):
                text+=' ' 
              if(symbol.property.detected_break.type==2):
                text+='\t'
              if(symbol.property.detected_break.type==5):
                text+='\n'
              if(symbol.property.detected_break.type==3):
                text+='\n'
    return text

def assemble_word(word):
    assembled_word=""
    for symbol in word.symbols:
        assembled_word+=symbol.text
    return assembled_word

#Finding location of each label in the document
def find_word_location(document,word_to_find):
    loc=[]
    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    assembled_word=assemble_word(word)
                    if(assembled_word==word_to_find):
                        loc.append(word.bounding_box)
    return loc

#Comparing double-worded label locations 
def check_loc(keys):
    loc=[]
    label=[]
    flag=0
    i=0
    substr=""
    for ch in keys:
      if (ch==' '):
        label.append(substr)
        substr=""
        flag+=1
      else:
        substr+=ch

    if(flag==1):
      loc.append(find_word_location(document,label[0]))
      return (loc[0][0].vertices[0].x,loc[0][0].vertices[0].y)
     
    loc.append(find_word_location(document,label[0]))
    loc.append(find_word_location(document, label[1]))
     
    for i in range(0,len(loc[0])):
       for j in range(0,len(loc[1])):
            if (loc[0][i].vertices[0].y==loc[1][j].vertices[0].y):
              return (loc[1][j].vertices[0].x,loc[1][j].vertices[0].y)

#Finding data having approx same y values - using adjustment factor
def find_data_right(res,x,vertice,y_adjust=0.01):
  text=""
  for i in range(0,len(res)):
    if (res[i][1]==vertice or res[i][1] in range(int(vertice-y_adjust*vertice),int(vertice+y_adjust*vertice))):
      text+=res[i][4]
  return(text)

def find_data_down(res,x,y,x_adjust=0.10,y_adjust=0.25):
  text=""
  for i in range(0,len(res)):
    if ((res[i][1] in range(y,int(y+y_adjust*y)))and (res[i][0] in range(int(x-x_adjust*x),int(x+x_adjust*x)))):
      text+=res[i][4]
  return(text)

#location=find_word_location(document,'Invoice')
#print(location)
#location=find_word_location(document,'Number')
#print(location[0].vertices[0].x)
#bounds = get_document_bounds(response, FeatureType.BLOCK)
#draw_boxes(image, bounds, 'red') 

if __name__== "__main__":

  #Argument Parsing
  parser = argparse.ArgumentParser()
  parser.add_argument('-input','--input',dest='input')
  parser.add_argument('-file','--template',dest='file')
  parser.add_argument('-output','--output',dest='output')
  parser.add_argument('-x','--x_adjust',dest='x_adjust',default=0.10)
  parser.add_argument('-y','--y_adjust',dest='y_adjust',default=0.01)

  args = parser.parse_args()
  error_log=open("errorlog.txt","w+")
#Loading template into a dictionary 
  with open(args.file) as file:
        datastore = json.load(file)

  f=0
  pdffiles = []
  for file in glob.glob(args.input+"/*.pdf"):
    pdffiles.append(file)
    print(pdffiles[f])
    pages = convert_from_path((pdffiles[f]), 500)
    f+=1
    for page in pages:
      page.save('eg.jpg','JPEG')
      image_file='eg.jpg'
      image  = Image.open(image_file)

      client = vision.ImageAnnotatorClient()
      with io.open(image_file,'rb') as image_file1:
              content = image_file1.read()
      content_image = types.Image(content=content)
      response = client.document_text_detection(image=content_image)
      #storing the response obtained into document
      document = response.full_text_annotation

      
      bounds = get_document_bounds(response,FeatureType.WORD)#Word list
      bound=get_document_bounds(response,FeatureType.BLOCK)#Blocks list
      draw_boxes(image,bounds)
      draw_blocks(image,bound)
      # x,y=check_loc("Product Description ")
      # print("product description",find_data_down(block,x,y))

      right=datastore["right"]
      down=datastore["down"]
      
      

      #Searching for data to the right of label
      for key,values in right.items():
        if(check_loc(key)==None):
         #Error log- key not found
         error_log.write((key+" not found in"+pdffiles[f-1]))
         continue
        x,y=check_loc(key)
        data_raw=find_data_right(res,x,y,args.y_adjust)
        if(data_raw==None):
          #Write error message into log- data not found
          error_log.write(("Data corresponding to"+key+" not found in"+pdffiles[f-1]))
          continue
        if(values==""):
          data=data_raw
        else:
          if(re.search(values,data_raw)==None): 
            #If data of correct format isn't found - data not found error message 
            error_log.write(("Data corresponding to"+key+" does not match given format in"+pdffiles[f-1]))
            continue
          else:
            data= re.search(values,data_raw).group()
        print(key,data,"\n")
        output[key]=data
        
          

      #Searching for values below the table
      for key,values in down.items():
        if(check_loc(key)==None):
          error_log.write((key+" not found in"+pdffiles[f-1]))
          continue
        x,y=check_loc(key)
        data_raw=find_data_down(block,x,y)
        if(data_raw==None):
          #Write error message into log- data not found
          error_log.write(("Data corresponding to"+key+" not found in"+pdffiles[f-1]))
          continue
        if (values ==""):
          data=data_raw
        else:
          if(re.search(values,data_raw)==None):
            error_log.write(("Data corresponding to"+key+" does not match given format in"+pdffiles[f-1]))
            continue
          else:
            data= re.search(values,data_raw).group()
        print(key,data)
        output[key]=data
      #Appending json block into output.json
    with open(args.output,'a') as file:
      json.dump(output,file)